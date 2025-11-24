# 题目 C：HTTP/3／CDN 协议分析工具（含 Few-Shot 扩展）

## 一、任务背景

随着边缘网络全面拥抱 HTTP/3（基于 QUIC 的 UDP 传输），CDN 的边缘回源链路出现了新的性能与可观测性需求：多路复用无队头阻塞、0-RTT 建连、连接迁移、拥塞控制算法（如 BBR/Cubic）带来更复杂的时延与吞吐动态。

为便于跨团队调试与快速定位问题，公司定义了简化版 **Edge-Proto v1.x** 日志格式，用于记录边缘节点与源站交互摘要（请求方法、路径、状态码、收发字节、往返时延 RTT、拥塞算法、QUIC 版本等）。

日志有以下特点：

- 来自边缘节点的 HTTP/3 / QUIC 交互；
- 协议会演进（v1.0 → v1.1 …），字段可能新增；
- 数据质量不完美：存在坏行、未知字段、字段缺失。

你的任务是实现一个 **HTTP/3 / CDN 协议分析工具**：

- 能解析 Edge-Proto v1.0 / v1.1 日志；
- 能输出一组关键统计指标（JSON 格式）；
- 在面对“协议演进 + 脏数据”时保持 **前向可扩展** 与 **后向兼容**；
- 展示你如何使用 AI 助手（ChatGPT / Copilot 等）来完成" Few-Shot 扩展"。

---

## 二、程序接口规范（必读！）

**为确保自动评测的一致性，所有提交必须遵循以下接口规范：**

### 命令行接口

**Python 实现：**
```bash
python -m edge_proto_tool.main <输入文件路径>
```

**Go 实现：**
```bash
./edge_proto_tool <输入文件路径>
```

或者使用 `--output` 参数指定输出文件：

```bash
python -m edge_proto_tool.main <输入文件路径> --output <输出文件路径>
```

### 输出格式要求

程序必须输出 JSON 格式的统计结果，包含以下**精确字段**：

```json
{
  "total_requests": 2468,
  "error_rate": 0.09,
  "avg_rtt_ms": 27.1,
  "top_congestion": "bbr"
}
```

**字段说明：**

| 字段名 | 类型 | 说明 | 格式要求 |
|--------|------|------|----------|
| `total_requests` | 整数 | 有效请求总数（不含坏行） | 精确值 |
| `error_rate` | 浮点数 | 4xx/5xx 错误比例 | 0.0-1.0，保留 2 位小数 |
| `avg_rtt_ms` | 浮点数 | 平均往返时延（毫秒） | 保留 1 位小数 |
| `top_congestion` | 字符串 | 出现次数最多的拥塞算法 | 如 "bbr", "cubic" |

**输出方式：**

- **方式 A**（默认）：输出到 stdout
  ```bash
  python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
  # 直接在终端打印 JSON
  ```

- **方式 B**：输出到文件
  ```bash
  python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log --output results/A_stats.json
  # JSON 写入指定文件
  ```

### 错误处理要求

1. **坏行处理**：遇到格式错误的行时，程序**不得中断**
2. **警告输出**：对于无效行，应向 stderr 输出警告信息（包含行号和原因）
3. **跳过无效行**：坏行不计入统计，但需要在 stderr 中报告

**示例 stderr 输出：**
```
Warning line 163: insufficient fields: expected 10-11, got 7
Warning line 290: insufficient fields: expected 10-11, got 9
```

### 目录结构建议

为了便于评测脚本自动检测，建议采用以下目录结构：

**Python：**
```
your-submission/
  edge_proto_tool/
    __init__.py
    main.py
    parser.py
  requirements.txt
  README.md
```

**Go：**
```
your-submission/
  edge_proto_tool     # 编译后的二进制文件
  main.go
  parser.go
  go.mod
  README.md
```

### 测试你的程序

在提交前，请确保你的程序能在 sample 数据集上正常运行：

```bash
# Python
python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
python -m edge_proto_tool.main data/sample/edge_proto_v1_B.log
python -m edge_proto_tool.main data/sample/edge_proto_v1_1_C.log

# Go
./edge_proto_tool data/sample/edge_proto_v1_A.log
./edge_proto_tool data/sample/edge_proto_v1_B.log
./edge_proto_tool data/sample/edge_proto_v1_1_C.log
```

**重要提示：** 自动评测将使用隐藏数据集测试你的程序，该数据集与 sample 数据格式相同，但内容不同。

---

## 三、数据集说明

本仓库包含一个公开样例数据集，用于本地开发与调试：

```text
data/sample/
  ├── edge_proto_v1_A.log       # 数据集 A：常规 HTTP/3 流量
  ├── edge_proto_v1_B.log       # 数据集 B：含错误状态、多拥塞算法
  ├── edge_proto_v1_1_C.log     # 数据集 C：v1.1 扩展，新增缓存状态字段
  └── MANIFEST.json             # 简要说明
```

### 1. Edge-Proto v1.0

`edge_proto_v1_A.log` 和 `edge_proto_v1_B.log` 中的日志行为 **v1.0**，每行示例：

```text
2025-03-01T10:01:02Z,33,GET,/index.html,200,1520,56321,21,bbr,q050
```

字段大致包含：

* `timestamp`：时间戳（ISO8601，Z 结尾）
* `stream_id`：QUIC 流 ID
* `method`：HTTP 方法（GET/POST/…）
* `path`：URL 路径
* `status`：HTTP 状态码
* `bytes_sent`：发送字节数
* `bytes_recv`：接收字节数
* `rtt_ms`：往返时延（毫秒）
* `congestion`：拥塞控制算法（如 `bbr` / `cubic`）
* `quic_version`：QUIC 版本（如 `q046` / `q050`）

日志中可能混入：

* 字段数不对的坏行；
* 附加未知字段的行；
* 注释行（以 `#` 开头，尤其在 v1.1 样例中）。

### 2. Edge-Proto v1.1（扩展示例）

`edge_proto_v1_1_C.log` 中为 **v1.1**，示例：

```text
# Edge-Proto v1.1
2025-03-01T10:01:02Z,33,GET,/index.html,200,1520,56321,21,bbr,q050,HIT
2025-03-01T10:01:03Z,35,GET,/api/user,503,980,312,14,bbr,q046,MISS
2025-03-01T10:01:04Z,37,POST,/upload,200,3210,12893,42,cubic,q050,BYPASS
```

与 v1.0 相比，多了一个末尾字段（你需要自行归纳其字段名与含义，例如 `edge_cache_status`）。

---

## 四、你的任务

你可以使用 **Python 或 Go** 实现，语言自选。建议目录结构如下（也可以自行组织）：

```text
src/
  edge_proto_tool/
    main.py           # 或 main.go
    parser.py         # 或 parser.go
    ...
data/
  sample/
    ...
```

### 任务 1：实现日志解析与统计（Edge-Proto v1.0）

编写程序，完成以下功能：

1. 解析 `data/sample/` 下的 v1.0 日志文件（A、B）；

2. 计算并输出以下统计指标（JSON，对不同文件分别输出即可）：

   ```json
   {
     "total_requests": 3000,
     "error_rate": 0.04,
     "avg_rtt_ms": 27.8,
     "top_congestion": "bbr"
   }
   ```

   其中：

   * `total_requests`：有效请求总数（坏行不计入）
   * `error_rate`：错误请求比例（例如 4xx/5xx 所占比例），0–1 浮点数
   * `avg_rtt_ms`：有效请求的平均 RTT（毫秒，建议保留 1 位小数或 2 位小数）
   * `top_congestion`：出现次数最多的拥塞算法名称

3. 遇到非法行或未知格式时：

   * 不得中断程序；
   * 在标准输出或日志中打印一条 **警告**（例如包含行号与原因）；
   * 跳过该行，不计入统计。

> 注意：请自行归纳字段含义和位置，不依赖题面给出的精确字段表。

---

### 任务 2：设计可扩展的解析结构

为了适应未来版本（例如 v1.2、v2.0）：

* 请将解析逻辑设计为 **可扩展 / 插件化**：

  * 可以通过类/接口/策略模式等方式拆分；
  * 避免将所有字段写死在一处的“巨大 if/else”；
* 考虑：

  * 新增字段时对旧版本的影响；
  * 未知字段如何处理；
  * 能否根据行的字段数量或头部注释自动识别版本。

你需要在 `README` 中简单说明你的设计思路。

---

### 任务 3：Few-Shot 扩展 —— 支持 Edge-Proto v1.1

使用 `edge_proto_v1_1_C.log`（包含 v1.1 日志），完成：

1. **使用 AI 助手（如 ChatGPT / Copilot）进行 Few-Shot 推断**：

   * 利用题目给出的 v1.1 示例行；
   * 让 AI 帮你推断新增字段的含义、位置、可能取值；
   * 设计或改造你的解析器，使其能同时支持 v1.0 和 v1.1。

2. 扩展解析器，使其满足：

   * 能正确解析 v1.0 & v1.1；
   * v1.1 行中，能解析出新增字段（例如 `edge_cache_status`）；
   * 代码在面对未来继续增加字段时，尽量无需大改；
   * 遇到未知字段时保持稳健（警告 + 跳过或忽略）。

3. 在你的 `README` 中附上：

   * 你给 AI 助手的 **提示词（Prompt）**；
   * AI 返回的**关键结论**（可以是总结/提炼后的版本）；
   * 你是如何基于这些结论修改解析器的（用几句话说明即可）。

---

## 五、输出与提交要求

### 1. 程序输出

你可以选择：

* 方式 A：命令行工具

  * 示例：

    ```bash
    # 分别对三个文件做统计
    python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
    python -m edge_proto_tool.main data/sample/edge_proto_v1_B.log
    python -m edge_proto_tool.main data/sample/edge_proto_v1_1_C.log
    ```
  * 将 JSON 结果输出到 stdout。

* 方式 B：生成 JSON 文件

  * 例如：

    ```bash
    python -m edge_proto_tool.main \
      --input data/sample/edge_proto_v1_A.log \
      --output out/A_stats.json
    ```

评测时会用隐藏数据集调用你的程序，并对 JSON 进行比对，请在自述文件中清楚写明：

* 如何运行你的程序；
* 对某个输入文件，输出写到哪里、格式是什么。

### 2. 提交内容

请确保你的提交包括：

1. 源代码（Python/Go 任意，其它语言请先确认是否支持）；
2. 自述文件（README）：

   * 项目结构；
   * 字段解析与版本识别设计；
   * 使用 AI 助手的 Prompt 与简要说明；
   * 编译 / 运行 / 简单测试说明；
3. （可选）简单测试脚本或示例命令；
4. （可选加分）简单性能测试或错误场景说明。

---

## 六、评分参考（仅供考生参考，不含具体权重）

1. **功能正确性**：统计结果是否正确（基于隐藏数据集比对 JSON）；
2. **稳健性与扩展性**：坏行处理、未知字段处理、对 v1.1 的兼容能力，代码结构是否有利于未来扩展；
3. **AI 使用说明**：是否合理使用 Few-Shot 思路，Prompt 是否清晰，是否有解释“如何使用/修改 AI 输出”；
4. **工程规范**：目录结构、注释、可复现性（是否容易一键运行）。

---

## 七、快速开始（建议）

如果使用 Python，可以参考：

```bash
python -m venv .venv
source .venv/bin/activate      # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt

python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
```

祝你玩得开心，写出既健壮又优雅的解析工具 🙂


