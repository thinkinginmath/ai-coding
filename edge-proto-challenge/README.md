# 题目 C：HTTP/3／CDN 协议日志分析工具（含 Few-Shot 扩展）

## 一、任务背景

随着边缘网络全面拥抱 HTTP/3（基于 QUIC 的 UDP 传输），CDN 的边缘回源链路出现了新的性能与可观测性需求：多路复用无队头阻塞、0-RTT 建连、连接迁移、拥塞控制算法（如 BBR/Cubic）带来更复杂的时延与吞吐动态。

为便于跨团队调试与快速定位问题，公司定义了简化版 **Edge-Proto v1.x** 日志格式，用于记录边缘节点与源站交互摘要（请求方法、路径、状态码、收发字节、往返时延 RTT、拥塞算法、QUIC 版本等）。

> **本质上，这是一个日志分析工具**，用于解析兼容 HTTP/3／CDN 协议的日志文件并生成统计报告。

你的任务是实现一个 **HTTP/3 / CDN 协议日志分析工具**：

- 能解析 Edge-Proto v1.0 / v1.1 日志；
- 能输出一组关键统计指标（JSON 格式）；
- 在面对"协议演进 + 脏数据"时保持 **前向可扩展** 与 **后向兼容**；
- 展示你如何使用 AI 助手（ChatGPT / Copilot 等）来完成"Few-Shot 扩展"。

---

## 二、字段定义规范（重要！）

### Edge-Proto v1.0 字段定义（按顺序，共 10 个字段）

| 位置 | 字段名 | 类型 | 说明 | 有效值示例 |
|------|--------|------|------|------------|
| 1 | `timestamp` | 字符串 | ISO8601 时间戳 | `2025-03-01T10:00:00Z`（必须以 Z 结尾） |
| 2 | `stream_id` | 整数 | QUIC 流 ID | `167`, `3061` |
| 3 | `method` | 字符串 | HTTP 方法 | `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS` |
| 4 | `path` | 字符串 | URL 路径 | `/index.html`, `/api/user`（不能为空） |
| 5 | `status` | 整数 | HTTP 状态码 | `100-599` 范围内的整数 |
| 6 | `bytes_sent` | 整数 | 发送字节数 | `1259`, `8867` |
| 7 | `bytes_recv` | 整数 | 接收字节数 | `3623`, `54957` |
| 8 | `rtt_ms` | 整数 | 往返时延（毫秒） | `32`, `44` |
| 9 | `congestion` | 字符串 | 拥塞控制算法 | `bbr`, `cubic` |
| 10 | `quic_version` | 字符串 | QUIC 版本 | `q043`, `q046`, `q050`（必须以 q 开头） |

### Edge-Proto v1.1 字段定义（共 11 个字段）

在 v1.0 的基础上，末尾新增一个字段：

| 位置 | 字段名 | 类型 | 说明 | 有效值示例 |
|------|--------|------|------|------------|
| 11 | `edge_cache_status` | 字符串 | 边缘缓存状态 | `HIT`, `MISS`, `BYPASS` |

---

## 三、坏行定义与示例（重要！）

以下情况视为**坏行**，应跳过并输出警告，不计入统计：

### 1. 字段数量错误

```text
# 字段不足（只有 6 个字段）
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,

# 字段过多（12 个字段）
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbr,q050,HIT,UNKNOWN
```

### 2. 字段格式/类型错误

```text
# timestamp 格式错误（缺少日期部分）
2025-03T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbr,q050,HIT

# stream_id 不是数字
2025-03-01T10:10:00Z,str,GET,/assets/app.js,301,1484,4441,44,bbr,q050,HIT

# method 不是有效的 HTTP 方法
2025-03-01T10:10:00Z,4146,TRUE,/assets/app.js,301,1484,4441,44,bbr,q050,HIT

# path 为空
2025-03-01T10:10:00Z,4146,GET,,301,1484,4441,44,bbr,q050,HIT

# status 超出有效范围（>599）
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,999,1484,4441,44,bbr,q050,HIT

# bytes_sent 不是数字
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,app,4441,44,bbr,q050,HIT

# bytes_recv 不是数字
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,api,44,bbr,q050,HIT

# rtt_ms 不是数字
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,second,bbr,q050,HIT

# congestion 不是有效值
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbrbbr,q050,HIT

# quic_version 格式错误（不以 q 开头）
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbr,xq050,HIT

# edge_cache_status 不是有效值
2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbr,q050,HITT
```

### 3. 注释行

```text
# 以 # 开头的行是注释，应忽略（不计入坏行，也不计入有效行）
# 2025-03-01T10:10:00Z,4146,GET,/assets/app.js,301,1484,4441,44,bbr,q050,HIT
```

---

## 四、程序接口规范（必读！）

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

### 输出格式要求

程序必须输出 JSON 格式的统计结果，包含以下**精确字段**：

```json
{
  "total_requests": 498,
  "error_rate": 0.12,
  "avg_rtt_ms": 26.8,
  "top_congestion": "bbr"
}
```

**字段说明：**

| 字段名 | 类型 | 说明 | 格式要求 |
|--------|------|------|----------|
| `total_requests` | 整数 | 有效请求总数（不含坏行） | 精确值 |
| `error_rate` | 浮点数 | 4xx/5xx 错误比例 | 0.0-1.0，**保留 2 位小数** |
| `avg_rtt_ms` | 浮点数 | 平均往返时延（毫秒） | **保留 1 位小数** |
| `top_congestion` | 字符串 | 出现次数最多的拥塞算法 | `"bbr"` 或 `"cubic"` |

### 浮点数格式说明

- `error_rate`: 保留 2 位小数。例如：`0.10`（不是 `0.1`），`0.05`
- `avg_rtt_ms`: 保留 1 位小数。例如：`27.0`（不是 `27`），`53.8`

**注意：** 评分时会使用容差比较：
- `error_rate`: ±0.01 容差
- `avg_rtt_ms`: ±0.5 容差

### 错误处理要求

1. **坏行处理**：遇到格式错误的行时，程序**不得中断**
2. **警告输出**：对于无效行，应向 stderr 输出警告信息（包含行号和原因）
3. **跳过无效行**：坏行不计入统计，但需要在 stderr 中报告

**示例 stderr 输出：**
```
Warning line 163: insufficient fields: expected 10-11, got 7
Warning line 290: invalid stream_id: not a number
```

---

## 五、数据集说明

### 考试用数据集（sample）

```text
data/sample/
  ├── edge_proto_v1_A.log       # 数据集 A：v1.0 常规 HTTP/3 流量
  ├── edge_proto_v1_B.log       # 数据集 B：v1.0 含错误状态、多拥塞算法、坏行
  ├── edge_proto_v1_1_C.log     # 数据集 C：v1.1 扩展，新增缓存状态字段
  ├── edge_proto_v1_1_D.log     # 数据集 D：全坏行（用于测试鲁棒性）
  ├── expected_answers.json     # 参考答案
  └── MANIFEST.json             # 简要说明
```

### 参考答案

以下是 sample 数据集的**标准答案**，供考生验证程序正确性：

**edge_proto_v1_A.log (v1.0 常规流量):**
```json
{
  "total_requests": 498,
  "error_rate": 0.12,
  "avg_rtt_ms": 26.8,
  "top_congestion": "bbr"
}
```

**edge_proto_v1_B.log (v1.0 含错误):**
```json
{
  "total_requests": 492,
  "error_rate": 0.42,
  "avg_rtt_ms": 53.8,
  "top_congestion": "cubic"
}
```

**edge_proto_v1_1_C.log (v1.1 扩展):**
```json
{
  "total_requests": 498,
  "error_rate": 0.43,
  "avg_rtt_ms": 53.0,
  "top_congestion": "bbr"
}
```

**edge_proto_v1_1_D.log (全坏行):**
```json
{
  "total_requests": 0,
  "error_rate": 0.0,
  "avg_rtt_ms": 0.0,
  "top_congestion": ""
}
```

### 评分用数据集（hidden）

评分时将使用**隐藏数据集**，格式与 sample 完全一致，但内容不同。

---

## 六、评分标准

### 总分：100 分，60 分及以上为通过

| 数据集 | 分值 | 说明 |
|--------|------|------|
| Dataset A (v1.0 normal) | 20 分 | 常规 HTTP/3 流量 |
| Dataset B (v1.0 with errors) | 30 分 | 含错误状态码和坏行 |
| Dataset C (v1.1 extended) | 36 分 | v1.1 扩展格式 |
| Dataset D (all bad lines) | 14 分 | 全坏行，测试鲁棒性 |

### 评分方法

#### Dataset A/B/C 评分规则

每个数据集按 4 个输出字段分别计分，每个字段占该数据集分值的 25%：

- `total_requests`: 精确匹配
- `error_rate`: ±0.01 容差
- `avg_rtt_ms`: ±0.5 容差
- `top_congestion`: 精确匹配

#### Dataset D 评分规则（鲁棒性测试）

- Dataset D 包含 14 行，每行包含一种不同类型的错误
- 只检查 `total_requests` 字段
- 正确处理所有坏行时，`total_requests` 应为 0
- 每个未正确识别的坏行扣 1 分（根据 `total_requests` 值扣分）

---

## 七、你的任务

### 任务 1：实现日志解析与统计（Edge-Proto v1.0）

1. 解析 `data/sample/` 下的 v1.0 日志文件（A、B）
2. 计算并输出统计指标（JSON 格式）
3. 正确处理坏行（跳过并输出警告）

### 任务 2：设计可扩展的解析结构

- 将解析逻辑设计为**可扩展 / 插件化**
- 考虑新增字段时对旧版本的影响
- 在 README 中说明你的设计思路

### 任务 3：Few-Shot 扩展 —— 支持 Edge-Proto v1.1

1. 使用 AI 助手进行 Few-Shot 推断新增字段
2. 扩展解析器，使其同时支持 v1.0 和 v1.1
3. 在 README 中附上 Prompt 和 AI 返回的关键结论

---

## 八、提交要求

### 目录结构

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

```bash
# Python
python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
python -m edge_proto_tool.main data/sample/edge_proto_v1_B.log
python -m edge_proto_tool.main data/sample/edge_proto_v1_1_C.log
python -m edge_proto_tool.main data/sample/edge_proto_v1_1_D.log

# Go
./edge_proto_tool data/sample/edge_proto_v1_A.log
./edge_proto_tool data/sample/edge_proto_v1_B.log
./edge_proto_tool data/sample/edge_proto_v1_1_C.log
./edge_proto_tool data/sample/edge_proto_v1_1_D.log
```

---

## 九、Docker 开发环境

为确保统一的开发环境，我们提供了 Docker 镜像，包含 Python 3.11 和 Go 运行时。

**程序必须能在 Docker 环境中运行，输出 JSON 格式结果。**

### 使用 Docker Compose（推荐）

```bash
# 构建并启动开发环境
docker-compose up -d

# 进入容器
docker exec -it edge-proto-challenge bash

# 在容器内运行你的程序
python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
```

### 使用 Docker 命令

```bash
# 构建镜像
docker build -t edge-proto-challenge .

# 运行容器
docker run -it --rm \
  -v $(pwd)/submission:/workspace/edge_proto_tool \
  -v $(pwd)/results:/workspace/results \
  edge-proto-challenge bash
```

### 容器内环境

- **Python**: 3.11
- **Go**: 1.24
- **工作目录**: `/workspace`
- **数据目录**: `/workspace/data/sample/`

---

祝你顺利完成挑战！
