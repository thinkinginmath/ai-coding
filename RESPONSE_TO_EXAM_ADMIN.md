# 给考试管理员的回复

## 关于两道题目的自动评分方案

感谢您选择了这两道题目。我已经为两道题目都准备好了完整的自动评分系统。

---

## 一、后端题（HTTP/3/CDN 协议分析工具）

### 评分标准细节

已完善并实现**全自动评分系统**：

#### 1. 接口规范（已添加到 README）

**命令行接口要求：**
```bash
# Python
python -m edge_proto_tool.main <输入文件>

# Go
./edge_proto_tool <输入文件>
```

**输出格式要求（JSON）：**
```json
{
  "total_requests": 2468,
  "error_rate": 0.09,
  "avg_rtt_ms": 27.1,
  "top_congestion": "bbr"
}
```

所有考生必须输出这 4 个字段，字段名和格式必须完全一致。这样就避免了"各自实现造成无法跑统一的测试用例"的问题。

#### 2. 自动评分方式

✅ **方式：基于 JSON 输出比对**

优点：
- 最简单易行，不需要侵入考生代码
- 考生只需保证输出正确的 JSON 格式
- 不需要规定类名、函数名等内部实现
- 评分脚本直接运行程序，解析输出，与标准答案对比

评分脚本位置：`grading/edge_proto/grader.py`

#### 3. 评分细则（70分自动 + 30分人工）

**自动评分（70分）：**

| 数据集 | 版本 | 分值 | 说明 |
|--------|------|------|------|
| Dataset A | v1.0 | 20分 | 常规流量 |
| Dataset B | v1.0 | 25分 | 包含错误、多种拥塞算法 |
| Dataset C | v1.1 | 25分 | 扩展协议 |

每个数据集按字段正确性打分：
- `total_requests`：精确匹配（25%）
- `error_rate`：±0.01 误差容忍（25%）
- `avg_rtt_ms`：±0.5ms 误差容忍（25%）
- `top_congestion`：精确匹配（25%）

**人工评分（30分）：**
- 健壮性与扩展性（15分）：坏行处理、版本兼容、代码结构
- 代码质量与文档（15分）：AI 使用说明、README、代码规范

#### 4. 使用方法

```bash
cd grading/edge_proto

# 一次性准备：生成标准答案
python3 generate_ground_truth.py

# 评分单个考生
./run_grader.sh /path/to/candidate/submission

# 输出示例：
# Dataset: edge_proto_v1_A.log
#   Score: 100.0%
#   ✓ total_requests      actual=2468          expected=2468
#   ✓ error_rate          actual=0.09          expected=0.09
#   ✓ avg_rtt_ms          actual=27.1          expected=27.1
#   ✓ top_congestion      actual=bbr           expected=bbr
#   Points earned: 20.0 / 20
#
# FINAL SCORE (Correctness): 70.0 / 70
```

---

## 二、前端题（实时 API 延迟仪表盘）

### 关于自动化测试

**建议：使用自动化测试**

#### 理由：

1. **人工验证复杂度更高**
   - 需要打开每个考生的页面
   - 手动检查 localStorage
   - 手动计时验证 5 秒轮询
   - 手动检查图表子元素数量
   - 容易出现人为错误

2. **自动化测试反而更简单**
   - 框架已经搭好（Playwright）
   - 一个命令完成所有测试
   - 2-3 分钟 vs 人工 15-20 分钟
   - 结果客观一致

3. **考生不需要搭测试框架**
   - 考生只需实现功能
   - 我们的测试框架独立运行
   - 考生不需要写任何测试代码

### 评分标准细节

已完善并实现**全自动评分系统**：

#### 1. DOM 结构规范（已添加到 README）

**必需的 data-testid 属性：**

```html
<!-- 平均延迟 -->
<div data-testid="avg-latency">150.5</div>

<!-- 最大延迟 -->
<div data-testid="max-latency">305</div>

<!-- 阈值配置输入 -->
<input data-testid="threshold-input" type="number" />

<!-- 图表容器（子元素数量=数据点数量）-->
<div data-testid="chart">
  <div class="point"></div>
  <div class="point"></div>
  ...
</div>

<!-- 告警（仅当超过阈值时渲染）-->
<div data-testid="alert">Latency spike detected</div>
```

这样就能"确保各自实现能跑统一的测试用例"。

#### 2. Mock API Server

✅ **已提供完整的 Mock API 服务器**

考生不需要实现后端，只需要：
```bash
cd grading/frontend_dashboard
npm run api
```

Mock server 会在 `http://localhost:3001/metrics/latency` 提供测试数据。

#### 3. 自动测试内容（100分）

| 测试项 | 分值 | 说明 |
|--------|------|------|
| 平均延迟计算 | 10分 | 验证数值正确性 |
| 最大延迟计算 | 10分 | 验证数值正确性 |
| 告警显示逻辑 | 7.5分 | 超过阈值时显示 |
| 告警隐藏逻辑 | 7.5分 | 低于阈值时不显示 |
| 图表渲染 | 15分 | 子元素数量正确 |
| 轮询间隔 | 15分 | 每5秒请求一次 |
| 默认阈值 | 4分 | localStorage 初始化 |
| 阈值调整 | 4分 | 修改后保存 |
| 阈值参考线 | 4分 | 图表中显示 |
| 数据点高亮 | 4分 | 超过阈值的点高亮 |
| 阈值持久化 | 4分 | 刷新后保持 |
| 历史数据 | 10分 | 保留10分钟数据 |
| 错误提示 | 2.5分 | API失败显示错误 |
| 错误恢复 | 2.5分 | 失败后继续轮询 |

#### 4. 使用方法

```bash
# 终端1：启动考生的应用
cd /path/to/candidate/submission
npm install
npm start

# 终端2：运行自动评分
cd grading/frontend_dashboard
./run_grader.sh /path/to/candidate/submission 3000

# 输出示例：
# ✓ should display correct average latency: +10 points
# ✓ should display correct max latency: +10 points
# ✓ should show alert when max latency exceeds threshold: +7.5 points
# ...
# FINAL SCORE: 96.0 / 100
```

测试完成后，还可以查看详细报告：
```bash
npx playwright show-report
```

包含失败截图、网络日志、控制台输出等。

#### 5. 人工验证也足够清晰

如果您坚持人工验证，现在的 README 也已经足够清晰：

✅ **清晰描述了什么：**
- 每个必需的 DOM 元素及其 data-testid
- 每个功能的精确要求
- 如何用开发者工具验证：
  ```javascript
  // 检查 localStorage
  localStorage.getItem('latencyThreshold')

  // 检查元素
  document.querySelector('[data-testid="chart"]').children.length
  ```

**但我们强烈建议用自动化测试**，因为：
- 更快（2分钟 vs 15分钟）
- 更准确（不会漏检）
- 更公平（标准一致）

---

## 三、总结

### 后端题

✅ **评分方式：JSON 输出比对**
- 最容易实现自动评分
- 接口规范已明确（README 第二节）
- 评分脚本已完成并测试

### 前端题

✅ **推荐：自动化测试（Playwright）**
- 测试框架已搭好，不需要考生配置
- Mock API 已提供
- 全部 100 分自动评分
- 如需人工验证，README 也足够清晰

### 文件位置

- 评分策略总览：`GRADING_STRATEGY.md`
- 教师使用指南：`grading/INSTRUCTOR_GUIDE.md`
- 后端评分脚本：`grading/edge_proto/`
- 前端评分脚本：`grading/frontend_dashboard/`
- 考生规范：
  - 后端：`edge-proto-challenge/README.md`（第二节）
  - 前端：`frontend-live-latency-dashboard/README.md`（DOM结构要求）

### 快速上手

**后端：**
```bash
cd grading/edge_proto
python3 generate_ground_truth.py
./run_grader.sh <考生目录>
```

**前端：**
```bash
cd grading/frontend_dashboard
npm install
npx playwright install chromium
./run_grader.sh <考生目录> 3000
```

所有代码已经写好并测试过，可以直接使用！
