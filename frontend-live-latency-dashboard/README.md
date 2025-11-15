# 前端挑战 — 实时 API 延迟仪表盘

## 概述

你的任务是使用 React 构建一个**实时更新的延迟仪表盘**。

你需要调用一个模拟后端 API：

```
GET /metrics/latency
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

## 需求

### 1. 展示最新的平均延迟

在 DOM 中渲染：

```html
<div data-testid="avg-latency">...</div>
```

### 2. 展示最大延迟

```html
<div data-testid="max-latency">...</div>
```

### 3. 每 5 秒轮询一次

组件挂载时请求 `/metrics/latency`，之后每隔 5 秒再次请求。

### 4. 迷你折线图（Sparkline）

可以使用任意绘图方式。

DOM 元素**必须**存在：

```html
<div data-testid="chart">
  <!-- 1 DOM element per data point -->
</div>
```

评分脚本会检查子元素数量，而不是图形外观。

### 5. 延迟峰值警报

如果**最大延迟 > 300**，显示：

```html
<div data-testid="alert">Latency spike detected</div>
```

否则**不要渲染**该警报 div。

### 6. 可配置阈值与历史趋势

* 在首次加载时将默认阈值设为 300 毫秒，并在浏览器 `localStorage` 中持久化。
* 提供 UI（输入框或滑块等）让用户调整阈值，更新后需要写入 `localStorage` 并立即影响页面。
* 图表需展示最近 10 分钟以内的数据，并显示一条表示当前阈值的参考线。
* 阈值线以上的节点需要高亮（颜色或样式均可），以便快速定位峰值。
* 处理数据请求失败的情况，显示用户可见的错误提示或退避重试策略。

---

## 可用工具

* React（CRA / Vite / Next.js）
* 任意图表库或自定义 SVG
* Fetch、Axios、SWR、TanStack Query 等

---

## 测试内容

我们会使用自动化 DOM 测试：

* `avg-latency` 中的值正确
* `max-latency` 中的值正确
* `alert` 仅在出现峰值时渲染
* 迷你折线图的节点数量正确
* 轮询间隔确实为 5 秒

---

## 提交

提交一个可运行的 React 项目，并在 `README` 中说明：

* 如何安装
* 如何运行
* 给审核者的其他说明
