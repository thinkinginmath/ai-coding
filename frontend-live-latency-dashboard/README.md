# 前端挑战 — 实时 API 延迟仪表盘

## 概述

你的任务是使用 React 构建一个**实时更新的延迟仪表盘**。

你需要调用一个模拟后端 API：

```
GET http://localhost:3001/metrics/latency
```

它会返回一个对象数组：

```json
[
  { "ts": 1718345000, "latency": 120 },
  { "ts": 1718345001, "latency": 118 },
  ...
]
```

每次请求都会返回一套新的数据。

---

## 模拟 API 服务器（重要）

**我们已经为你准备好了模拟 API 服务器！** 你不需要实现后端，只需运行我们提供的 mock server：

### 启动 Mock API Server

```bash
# 进入 grading 目录
cd grading/frontend_dashboard

# 安装依赖（首次运行）
npm install

# 启动 mock server（默认端口 3001）
npm run api
```

Mock server 将在 `http://localhost:3001` 上运行，提供以下端点：

- `GET /metrics/latency` - 返回延迟数据数组
- `GET /health` - 健康检查

### 在你的 React 应用中使用

```javascript
// 在组件中调用 API
useEffect(() => {
  const fetchMetrics = async () => {
    const response = await fetch('http://localhost:3001/metrics/latency');
    const data = await response.json();
    // data 是一个数组: [{ ts: number, latency: number }, ...]
    setMetrics(data);
  };

  fetchMetrics(); // 初始加载
  const interval = setInterval(fetchMetrics, 5000); // 每 5 秒轮询

  return () => clearInterval(interval);
}, []);
```

---

## DOM 结构要求（必读！）

**为了支持自动评测，你的应用必须使用以下 `data-testid` 属性：**

### 必需的 DOM 元素

#### 1. 平均延迟显示

```html
<div data-testid="avg-latency">150.5</div>
```

显示最新一次获取数据的平均延迟值（数字）。

#### 2. 最大延迟显示

```html
<div data-testid="max-latency">305</div>
```

显示最新一次获取数据的最大延迟值（数字）。

#### 3. 阈值配置输入框

```html
<input data-testid="threshold-input" type="number" value="300" />
```

允许用户修改告警阈值，变更后应保存到 `localStorage`。

#### 4. 图表容器

```html
<div data-testid="chart">
  <!-- 每个数据点对应一个子元素 -->
  <div class="data-point"></div>
  <div class="data-point"></div>
  ...
</div>
```

图表容器的**直接子元素数量**必须等于数据点数量。评分脚本会检查子元素数量，不检查视觉外观。

#### 5. 峰值警报（条件渲染）

```html
<div data-testid="alert">Latency spike detected</div>
```

**仅当**最大延迟超过当前阈值时，才渲染此元素。否则不要渲染（不是隐藏，而是不存在于 DOM 中）。

---

## 功能需求

### 1. 实时数据轮询

- 组件挂载时立即请求 `http://localhost:3001/metrics/latency`
- 之后每隔 **5 秒** 轮询一次
- 使用 `setInterval` 或其他定时器机制

### 2. 指标计算

从 API 返回的数据数组中计算：

- **平均延迟**：所有数据点的 `latency` 值的平均值
- **最大延迟**：所有数据点的 `latency` 值的最大值

### 3. 图表渲染

- 使用任意方式绘制图表（SVG、Canvas、CSS、图表库等）
- 图表必须包含：
  - 数据点（每个数据点对应一个 DOM 子元素）
  - 阈值参考线（视觉上标识阈值位置）
  - 高亮显示：超过阈值的数据点需要以不同颜色/样式高亮

### 4. 阈值配置

- **默认阈值**：300 毫秒
- **持久化**：首次加载时，将阈值保存到 `localStorage`（键名建议：`latencyThreshold`）
- **可配置**：提供输入框让用户修改阈值
- **即时生效**：修改阈值后，立即更新图表和告警状态
- **页面刷新保持**：重新加载页面后，阈值应从 `localStorage` 恢复

### 5. 历史数据管理

- 保留最近 **10 分钟** 的数据
- 每次轮询获取新数据后，合并到历史数据中
- 自动移除超过 10 分钟的旧数据

### 6. 错误处理

- API 请求失败时，显示用户可见的错误信息
- 不要因为单次请求失败而停止轮询
- 继续尝试后续请求

---

## 可用工具

* React（CRA / Vite / Next.js）
* 任意图表库或自定义 SVG
* Fetch、Axios、SWR、TanStack Query 等

---

## 自动评测说明

你的提交将通过自动化测试进行评分，测试将验证：

### 基础指标（20 分）
- ✓ 平均延迟计算正确
- ✓ 最大延迟计算正确

### 告警行为（15 分）
- ✓ 最大延迟超过阈值时显示告警
- ✓ 最大延迟低于阈值时不显示告警

### 图表渲染（15 分）
- ✓ 图表容器存在且包含正确数量的子元素

### 轮询机制（15 分）
- ✓ 每 5 秒轮询一次 API（±0.5 秒误差容忍）

### 阈值配置（20 分）
- ✓ 默认阈值 300 保存到 localStorage
- ✓ 修改阈值后更新 localStorage
- ✓ 图表中显示阈值参考线
- ✓ 超过阈值的数据点高亮显示
- ✓ 页面刷新后阈值保持

### 历史数据（10 分）
- ✓ 保留最近 10 分钟数据

### 错误处理（5 分）
- ✓ API 失败时显示错误信息
- ✓ 失败后继续轮询

**总分：100 分**

---

## 提交要求

### 1. 项目结构

确保你的项目可以正常启动：

```bash
cd your-submission/
npm install
npm start
```

应用应在 `http://localhost:3000` 上运行（或在 README 中说明端口）。

### 2. README 文档

在你的 `README.md` 中包含：

- **安装步骤**：如何安装依赖
- **运行步骤**：如何启动开发服务器
- **端口说明**：如果不是 3000，请说明实际端口
- **技术栈**：使用的库和工具（如 React, Chart.js, Recharts 等）

### 3. 测试你的应用

在提交前，请确保：

1. Mock API server 在 3001 端口运行
2. 你的应用在 3000 端口运行
3. 所有必需的 `data-testid` 属性都已添加
4. localStorage 阈值配置正常工作
5. 图表正确渲染且子元素数量与数据点匹配

### 4. 本地测试

你可以用浏览器开发者工具验证：

```javascript
// 控制台中检查 localStorage
localStorage.getItem('latencyThreshold')

// 检查 DOM 元素
document.querySelector('[data-testid="avg-latency"]')
document.querySelector('[data-testid="chart"]').children.length

// 检查轮询间隔（Network 标签）
// 每 5 秒应该看到一次 /metrics/latency 请求
```

---

## 快速开始

### 推荐的技术栈

- **React**: 核心框架（Create React App、Vite、Next.js 均可）
- **图表库**（可选）：Recharts、Chart.js、Victory、或自定义 SVG
- **HTTP 客户端**：fetch API、axios、或 SWR/React Query

### 示例代码结构

```
your-app/
  src/
    components/
      Dashboard.jsx        # 主仪表盘组件
      MetricsDisplay.jsx   # 指标显示
      LatencyChart.jsx     # 图表组件
      ThresholdControl.jsx # 阈值配置
    hooks/
      useMetrics.js        # 自定义 hook 处理轮询
    App.js
  public/
  package.json
  README.md
```

### 启动流程

```bash
# 1. 启动 mock API server（终端 1）
cd grading/frontend_dashboard
npm install
npm run api

# 2. 启动你的 React 应用（终端 2）
cd your-submission
npm install
npm start

# 3. 浏览器访问
# http://localhost:3000
```

祝你好运！

---

## Docker 开发环境

为确保统一的开发环境，我们提供了 Docker 镜像，包含 Node.js 20 和预配置的 Mock API Server。

### 使用 Docker Compose（推荐）

```bash
# 构建并启动开发环境
docker-compose up -d

# 进入容器
docker exec -it frontend-dashboard-challenge bash

# 在容器内启动 Mock API（终端 1）
cd /workspace/mock-api && node mock-api-server.js

# 在容器内创建和运行你的 React 应用（终端 2）
cd /workspace/submission
npx create-react-app my-dashboard
cd my-dashboard
npm start
```

### 使用 Docker 命令

```bash
# 构建镜像
docker build -t frontend-dashboard-challenge .

# 运行容器
docker run -it --rm \
  -p 3000:3000 -p 3001:3001 \
  -v $(pwd)/submission:/workspace/submission \
  frontend-dashboard-challenge bash
```

### 容器内环境

- **Node.js**: 20.x
- **工作目录**: `/workspace`
- **Mock API**: `/workspace/mock-api/mock-api-server.js`
- **你的代码**: `/workspace/submission/`

### 端口说明

- **3000**: React 开发服务器
- **3001**: Mock API Server
