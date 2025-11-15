
# 题目：DeepSeek → OpenAI SSE 协议适配网关

## 一、场景背景

公司正在搭建一个 **AI API 网关**，对外提供统一的 OpenAI 风格接口，对内可以对接不同厂商（DeepSeek、OpenAI、…）的模型服务。

当前需求：

* 上游只接了 **DeepSeek Chat Completion** 接口（启用 SSE 流式输出）；
* 对外却要暴露 **OpenAI 风格的 SSE 接口**，方便客户复用现有 SDK；
* 网关必须负责：

  * 协议适配（DeepSeek SSE → OpenAI 风格 SSE）；
  * 连接 & 流式错误处理（网络错误、上游返回错误、中途断流等）。

你的任务是实现一个 **最小可用版本** 的网关服务，用来适配：

```text
Client (OpenAI 风格请求/SSE)
   ↓
Your Gateway
   ↓
Upstream: DeepSeek Chat Completion SSE
```

---

## 二、上游 DeepSeek SSE 协议（简化说明）

本题假设上游 DeepSeek 使用（与官方文档一致的）**旧式 Chat Completion SSE**，形如：

```text
data: {"id": "1f633d8bfc032625086f14113c411638",
       "object": "chat.completion.chunk",
       "created": 1718345013,
       "model": "deepseek-chat",
       "system_fingerprint": "fp_a49d71b8a1",
       "choices": [
         {
           "index": 0,
           "delta": {"content": "", "role": "assistant"},
           "finish_reason": null,
           "logprobs": null
         }
       ],
       "usage": null}

data: {"id": "1f633d8bfc032625086f14113c411638",
       "object": "chat.completion.chunk",
       "created": 1718345013,
       "model": "deepseek-chat",
       "system_fingerprint": "fp_a49d71b8a1",
       "choices": [
         {
           "index": 0,
           "delta": {"content": "Hello", "role": "assistant"},
           "finish_reason": null,
           "logprobs": null
         }
       ]}

...

data: {"id": "1f633d8bfc032625086f14113c411638",
       "object": "chat.completion.chunk",
       "created": 1718345013,
       "model": "deepseek-chat",
       "system_fingerprint": "fp_a49d71b8a1",
       "choices": [
         {
           "index": 0,
           "delta": {"content": "", "role": null},
           "finish_reason": "stop",
           "logprobs": null
         }
       ],
       "usage": {
         "completion_tokens": 9,
         "prompt_tokens": 17,
         "total_tokens": 26
       }}

data: [DONE]
```

特点（本题默认前提）：

* 所有正常 chunk 的 `object` 均为 `"chat.completion.chunk"`；
* 文本内容在 `choices[0].delta.content` 中，可能是空字符串；
* `choices[0].delta.role`：

  * 首个 chunk 通常为 `"assistant"`；
  * 中间 chunk 可以不提供或复用上一个；
* `choices[0].finish_reason`：

  * 中间 chunk 为 `null`；
  * 最后一个为 `"stop"`；
* 最后一个 chunk 可能包含 `usage`；
* SSE termination 行为：额外一行：`data: [DONE]`。

评测时会通过一个 **模拟 DeepSeek 上游**（本地 HTTP 服务）来给出类似的 SSE 流。

---

## 三、下游 OpenAI 风格 SSE（本题规格）

你的网关对外暴露的是一个 **简化版 OpenAI Responses 风格 SSE**，事件类型如下：

* `response.created`
* `response.output_text.delta`
* `response.completed`
* `response.error`

### 3.1 事件：response.created

在 **收到第一个合法上游 chunk** 时（也就是首次拿到 `id` / `model` / `created`）：

```text
event: response.created
data: {
  "id": "<deepseek-id>",
  "model": "<对外暴露的模型名>",
  "created": <created-epoch-second>
}
```

要求：

* `id` 直接透传上游 `id`；
* `model` 可以直接使用上游 `model`，或在配置中映射为例如 `"gpt-4.1-compatible"`（自定，但要保持一致）；
* `created` 透传上游 `created` 字段。

### 3.2 事件：response.output_text.delta

对每一个 DeepSeek chunk，如果：

* `choices[0].delta.content` 为非空字符串，

则输出一条：

```text
event: response.output_text.delta
data: {
  "id": "<deepseek-id>",
  "role": "<delta.role 或默认为 'assistant'>",
  "delta": "<delta.content>"
}
```

要求：

* **流式输出**：收到一个 chunk，就尽快向下游转发；
* 如果 `delta.role` 缺失或为 `null`，按 `"assistant"` 处理即可；
* 不要求合并 token，可以一 token / 一 chunk 输出一条事件。

### 3.3 事件：response.completed

当你检测到 **最后一个 chunk** 时（`choices[0].finish_reason == "stop"`）：

```text
event: response.completed
data: {
  "id": "<deepseek-id>",
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": <来自上游 usage.completion_tokens, 若有>,
    "prompt_tokens": <来自上游 usage.prompt_tokens, 若有>,
    "total_tokens": <来自上游 usage.total_tokens, 若有>
  }
}
```

注意：

* 若上游没有 `usage` 字段，你可以省略整个 `usage` 或设为 `null`，但实现逻辑要**稳健**；
* 输出完 `response.completed` 后，正常关闭 SSE 连接。

### 3.4 事件：response.error

用于传递 **上游错误 / 流式异常**。本题建议至少支持以下几类：

#### 3.4.1 上游连接失败 / HTTP 错误（未进入 SSE）

例如：

* DNS 失败；
* TCP 连接失败；
* 上游返回 5xx / 4xx 且没有 SSE 流。

此时建议直接返回 **非 200 HTTP 响应**（例如 502），body 为 JSON：

```json
{
  "error": {
    "type": "upstream_connection_error",
    "message": "Failed to connect to DeepSeek upstream"
  }
}
```

（这里可以不使用 SSE，因为根本没进入流式阶段。）

#### 3.4.2 流式过程中断（中途断流）

如果在已经开始推送 SSE（已经发出 `response.created`）之后，上游连接意外中断（如网络断开、连接 reset），且没有收到 `finish_reason:"stop"` 的最终 chunk：

则需要向客户端推送一条 **SSE error 事件**，然后关闭连接：

```text
event: response.error
data: {
  "type": "upstream_stream_broken",
  "message": "Upstream SSE connection closed unexpectedly"
}
```

#### 3.4.3 上游返回结构化错误事件（可选）

如果你设计的上游模拟服务会发送类似：

```text
data: {"error": {"code": "rate_limit", "message": "Too many requests"}}
```

则网关应映射为：

```text
event: response.error
data: {
  "type": "upstream_error",
  "code": "rate_limit",
  "message": "Too many requests"
}
```

---

## 四、网关 HTTP 接口规范

你需要实现一个 HTTP 服务器，提供至少一个接口：

### 4.1 下游接口：`POST /v1/chat/completions`

请求体（简化版 OpenAI Chat Completion 请求）：

```json
{
  "model": "gpt-4.1-compatible",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": true
}
```

要求：

1. **必须支持流式模式**：当 `stream: true` 时：

   * HTTP 响应为 `Content-Type: text/event-stream`;
   * 按上文定义的事件规范逐条写出 SSE 事件；
2. 允许忽略部分不需要的字段（如 `temperature`、`top_p` 等），但不能因为未知字段而报错；
3. 本题不要求非流式模式（`stream: false`），可以按 400/501 返回「未实现」。

### 4.2 上游调用：DeepSeek Chat Completion SSE

你可以假定上游地址通过环境变量给出，例如：

* `UPSTREAM_BASE_URL=http://localhost:9001`

网关需要：

* 将下游请求转换为上游请求：

  * `POST $UPSTREAM_BASE_URL/v1/chat/completions`
  * body 中至少包含：

    * `model`（映射到上游 DeepSeek 模型，如 `"deepseek-chat"`）
    * `messages`（透传或简单映射）
    * `stream: true`
* 以 SSE 方式读取上游响应，并按照第三节的规则进行转换与下发。

真实评测环境中会提供一个 **模拟 DeepSeek 上游服务**，行为大致包括：

* 正常返回流式 token；
* 返回 HTTP 5xx；
* 中途断流；
* 返回结构化错误。

---

## 五、实现要求 & 提交内容

### 5.1 必须实现的内容

* 一个可运行的 HTTP 服务：

  * 启动命令需写在 `README` 中；
  * 可以使用任意语言 / Web 框架（Python / Go / Node.js / …）；
* 按规范实现：

  * `/v1/chat/completions` 流式 SSE 接口；
  * 上游 DeepSeek SSE 调用；
  * DeepSeek → OpenAI SSE 事件映射；
  * 基本错误处理（连接失败、上游 HTTP 错误、中途断流）。

### 5.2 提交内容

至少包括：

1. 源代码；
2. `README.md`，包含：

   * 启动服务的命令（包含依赖安装方式）；
   * 如何配置上游 `UPSTREAM_BASE_URL`；
   * 若提供本地调试用的 mock DeepSeek 服务，也写明启动方式；
   * **AI 使用说明**（见下一节）；
3. （可选）简单的本地测试脚本（curl / httpie / Python 脚本均可）。

---

## 六、AI 辅助使用要求（必填）

本题允许、鼓励你使用 ChatGPT / Copilot 等 AI 辅助工具，但需要你展示你是 **在驱动 AI 完成工程设计，而不是简单复制粘贴**。

在你的 `README.md` 中，请补充一个小节，例如：

> ### AI 助手使用说明
>
> * 我使用了 ChatGPT 来生成 SSE 解析和事件映射的代码骨架；
> * 代表性 Prompt 示例：
>
>   * 「请根据下面的 SSE 协议说明，用 Python 写一个从上游事件到下游事件的转换器…」
> * 对 AI 输出的修改点：
>
>   * 原代码没有处理连接中断时的错误事件，我手动增加了 `try/except` 和 `response.error`；
>   * 原代码将所有 chunk 缓存在内存中再输出，我改成了边读边写（真正流式）。

此部分会作为评分的一部分。

---

## 七、评分参考维度（示意）

> 具体权重可由组织方自由调整，此处为建议项：

1. **功能正确性（≈40%）**

   * 正确调用上游；
   * 对正常 SSE 流生成正确的 `response.created` / `response.output_text.delta` / `response.completed`；
   * 对错误场景生成正确的 `response.error` 或 HTTP 错误响应。

2. **鲁棒性与工程性（≈30%）**

   * 中途断流处理是否合理；
   * 解析错误 / JSON 解析异常是否会导致整个进程崩溃；
   * 是否真正实现了“边读边写”的流式行为（而不是读完再一次性输出）。

3. **AI 使用与说明（≈20%）**

   * Prompt 是否清晰、体现思路；
   * 是否对 AI 生成代码做了自己的取舍与修改；
   * README 中是否有简要的反思：AI 的输出哪里不够好、你怎么修正的。

4. **代码与项目结构（≈10%）**

   * 代码是否易读；
   * 目录组织是否合理；
   * 是否易于在评测环境中启动与运行。

