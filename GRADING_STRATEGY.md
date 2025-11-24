# Auto-Grading Strategy for AI Coding Challenges

## Overview

This document outlines the auto-grading approach for the two selected challenges:
1. **Backend: HTTP/3/CDN Protocol Analysis Tool** (edge-proto-challenge)
2. **Frontend: Real-time API Latency Dashboard** (frontend-live-latency-dashboard)

---

## 1. Backend Challenge: edge-proto-challenge

### API Specification

To ensure uniform testing, candidates must follow this interface specification:

#### Command Line Interface

**Python:**
```bash
python -m edge_proto_tool.main <input_file> [--output <output_file>]
```

**Go:**
```bash
./edge_proto_tool <input_file> [-output <output_file>]
```

#### Output Format

**Option A: stdout (default)**
```bash
python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log
```
Outputs JSON to stdout:
```json
{
  "total_requests": 500,
  "error_rate": 0.12,
  "avg_rtt_ms": 27.3,
  "top_congestion": "bbr"
}
```

**Option B: file output**
```bash
python -m edge_proto_tool.main data/sample/edge_proto_v1_A.log --output results/A_stats.json
```
Writes JSON to specified file.

#### Required JSON Fields

All submissions must output exactly these fields:

| Field | Type | Description | Format |
|-------|------|-------------|--------|
| `total_requests` | integer | Number of valid requests (excluding bad lines) | Exact count |
| `error_rate` | float | Ratio of 4xx/5xx responses | 0.0 to 1.0, 2 decimal places |
| `avg_rtt_ms` | float | Average RTT in milliseconds | 1-2 decimal places |
| `top_congestion` | string | Most frequent congestion algorithm | "bbr", "cubic", etc. |

### Auto-Grading Process

#### Test Datasets
- **Sample datasets** (`data/sample/`): 500 lines each, provided to candidates
- **Hidden datasets** (`data/hidden/`): 2500 lines each, used for final grading

#### Grading Script Workflow

```python
for dataset in [A, B, C]:
    1. Run candidate's program on hidden dataset
    2. Parse output JSON
    3. Compare against ground truth JSON
    4. Calculate accuracy score per field
    5. Check for robustness (stderr warnings for bad lines)
```

#### Scoring Breakdown (100 points total)

**Correctness (70 points)**
- Dataset A (v1.0 normal): 20 points
- Dataset B (v1.0 errors): 25 points
- Dataset C (v1.1 extended): 25 points

Per dataset:
- `total_requests`: exact match (25%)
- `error_rate`: within ±0.01 (25%)
- `avg_rtt_ms`: within ±0.5ms (25%)
- `top_congestion`: exact match (25%)

**Robustness (15 points)**
- Handles bad lines without crashing (5 points)
- Outputs warnings to stderr for invalid lines (5 points)
- Supports both v1.0 and v1.1 formats (5 points)

**Code Quality & Documentation (15 points)**
- Extensible design (plugin/strategy pattern) (5 points)
- AI usage documentation (prompt + explanation) (5 points)
- Clear README with setup/run instructions (5 points)

### Ground Truth Generation

Need to create reference implementation or manually verify results:

```bash
# Generate expected results for grading
python grading/generate_ground_truth.py \
  --input edge-proto-challenge/data/hidden/ \
  --output grading/edge_proto_expected.json
```

---

## 2. Frontend Challenge: frontend-live-latency-dashboard

### Recommendation: Automated Testing

**Answer to exam admin's question:**
Yes, automated testing is strongly recommended for frontend grading. Reasons:
- Large number of candidates (manual review doesn't scale)
- Objective criteria (DOM structure, calculations, timing)
- Playwright/Puppeteer can verify all requirements programmatically
- More consistent and fair than manual evaluation

### API Specification

#### Mock API Server

Provide a mock server that candidates must run alongside their app:

```bash
# Start mock server on port 3001
node grading/mock-api-server.js
```

**Endpoint:** `GET http://localhost:3001/metrics/latency`

**Response format:**
```json
[
  { "ts": 1718345000, "latency": 120 },
  { "ts": 1718345001, "latency": 118 },
  { "ts": 1718345002, "latency": 305 }
]
```

The mock server should:
- Return different data on each request (simulating real-time updates)
- Return predictable sequences for testing (controlled by seed)
- Support error injection for testing error handling

#### Required DOM Structure

Candidates must implement these exact `data-testid` attributes:

```html
<div data-testid="avg-latency">125.5</div>
<div data-testid="max-latency">305</div>
<div data-testid="alert">Latency spike detected</div> <!-- Only when max > threshold -->
<div data-testid="chart">
  <!-- Child elements: one per data point -->
</div>
<input data-testid="threshold-input" type="number" />
```

### Auto-Grading Process

#### Test Scenarios

**Test 1: Basic Metrics (20 points)**
- Load page, wait for first data fetch
- Verify `avg-latency` displays correct average
- Verify `max-latency` displays correct maximum
- Values must match server response within 0.1ms

**Test 2: Alert Behavior (15 points)**
- Mock data with max < 300: alert should NOT exist
- Mock data with max > 300: alert must exist with correct text
- Alert must appear/disappear dynamically

**Test 3: Chart Rendering (15 points)**
- Verify `chart` container exists
- Count child elements = number of data points in response
- Visual appearance not graded (only DOM structure)

**Test 4: Polling Interval (15 points)**
- Track API requests over 30 seconds
- Verify requests occur every 5 seconds (±0.5s tolerance)
- Should be exactly 6 requests in 30 seconds

**Test 5: Threshold Configuration (20 points)**
- Verify default threshold = 300 in localStorage
- Change threshold via input, verify localStorage updated
- Verify threshold line appears in chart
- Verify data points above threshold are highlighted
- Reload page, verify threshold persists

**Test 6: Historical Data (10 points)**
- Verify chart shows last 10 minutes of data
- Poll multiple times, verify old data retained
- Verify data older than 10 minutes removed

**Test 7: Error Handling (5 points)**
- Mock API failure (500 error)
- Verify error message displayed to user
- Verify app doesn't crash, continues polling

#### Grading Script Implementation

```javascript
// Playwright test structure
test('Basic metrics calculation', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(1000); // Wait for initial fetch

  const avgText = await page.locator('[data-testid="avg-latency"]').textContent();
  const avg = parseFloat(avgText);

  expect(avg).toBeCloseTo(expectedAvg, 0.1);
});
```

### Setup Requirements for Candidates

Update README to specify:
1. Run mock API server on port 3001
2. Run frontend app on port 3000
3. Exact commands to start both services
4. No need to implement backend - use provided mock server

---

## Implementation Files to Create

### Backend Grading
1. `grading/edge_proto/grader.py` - Main grading script
2. `grading/edge_proto/generate_ground_truth.py` - Calculate expected results
3. `grading/edge_proto/expected_results.json` - Ground truth data
4. `grading/edge_proto/run_tests.sh` - Batch testing script

### Frontend Grading
1. `grading/frontend_dashboard/mock-api-server.js` - Mock API with controlled data
2. `grading/frontend_dashboard/grader.spec.js` - Playwright test suite
3. `grading/frontend_dashboard/package.json` - Dependencies
4. `grading/frontend_dashboard/run_tests.sh` - Automated test runner

### Documentation Updates
1. `edge-proto-challenge/README.md` - Add API specification section
2. `frontend-live-latency-dashboard/README.md` - Add mock server instructions
3. `GRADING.md` - Instructor guide for running graders

---

## Execution Instructions

### Backend Grading
```bash
cd grading/edge_proto
./run_tests.sh <candidate_submission_dir>
# Outputs: score breakdown + detailed report
```

### Frontend Grading
```bash
cd grading/frontend_dashboard
npm install
./run_tests.sh <candidate_submission_dir>
# Outputs: Playwright test report + score
```

---

## Advantages of This Approach

### Backend
- **Objective**: JSON comparison eliminates subjective judgment
- **Scalable**: Automated execution for 100+ submissions
- **Clear**: Exact API specification prevents ambiguity
- **Fair**: Same test data and criteria for all candidates

### Frontend
- **Comprehensive**: Tests all requirements programmatically
- **Fast**: 2-3 minutes per submission vs 15-20 minutes manual
- **Reliable**: No human error in verification
- **Demonstrable**: Test failures show exactly what's wrong

### Both
- **Reproducible**: Instructors can re-run grading anytime
- **Transparent**: Candidates can test locally before submission
- **Maintainable**: Easy to add new test cases or adjust scoring
