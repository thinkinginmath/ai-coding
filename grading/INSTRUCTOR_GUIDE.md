# Instructor Guide - Auto-Grading for AI Coding Challenges

This guide explains how to use the automated grading systems for the two selected challenges.

---

## Overview

We've prepared **fully automated** grading systems for:

1. **Backend Challenge**: edge-proto-challenge (HTTP/3/CDN Protocol Analysis Tool)
2. **Frontend Challenge**: frontend-live-latency-dashboard (Real-time API Latency Dashboard)

Both systems provide:
- **Objective scoring** based on test results
- **Detailed reports** showing what passed/failed
- **Fast execution** (1-3 minutes per submission)
- **Reproducible results**

---

## Prerequisites

### System Requirements

- **Python 3.8+** (for backend grading)
- **Node.js 16+** and npm (for frontend grading)
- **Bash shell** (Linux/macOS, or WSL/Git Bash on Windows)

### Initial Setup

```bash
# Clone or navigate to the repository
cd /path/to/ai-coding

# Backend: Verify Python and generate ground truth
python3 --version
cd grading/edge_proto
python3 generate_ground_truth.py

# Frontend: Install dependencies
cd ../frontend_dashboard
npm install
npx playwright install chromium
```

---

## Backend Challenge Grading

### Preparation

The grading system uses hidden test data located in `edge-proto-challenge/data/hidden/`.

**Generate expected results (one-time setup):**
```bash
cd grading/edge_proto
python3 generate_ground_truth.py
```

This creates `expected_results.json` with correct answers.

### Grading a Submission

#### Method 1: Using the run script (recommended)

```bash
cd grading/edge_proto
./run_grader.sh /path/to/candidate/submission
```

#### Method 2: Direct Python invocation

```bash
cd grading/edge_proto
python3 grader.py /path/to/candidate/submission
```

### What the Grader Checks

The grader automatically:
1. **Detects the program type** (Python or Go)
2. **Finds the executable** (looks for standard locations)
3. **Runs on 3 hidden datasets**:
   - Dataset A (v1.0 normal): 20 points
   - Dataset B (v1.0 with errors): 25 points
   - Dataset C (v1.1 extended): 25 points
4. **Compares output** against expected results
5. **Checks each field**:
   - `total_requests`: exact match
   - `error_rate`: ±0.01 tolerance
   - `avg_rtt_ms`: ±0.5ms tolerance
   - `top_congestion`: exact match

### Understanding the Output

```
Edge-Proto Challenge Auto-Grader
Submission: candidate_123
======================================================================

✓ Detected python program: python3 -m edge_proto_tool.main

Dataset: edge_proto_v1_A.log
  Score: 100.0%
  ✓ total_requests      actual=2468          expected=2468
  ✓ error_rate          actual=0.09          expected=0.09
  ✓ avg_rtt_ms          actual=27.1          expected=27.1
  ✓ top_congestion      actual=bbr           expected=bbr
  ✓ Program produced warnings for bad lines
  Points earned: 20.0 / 20

Dataset: edge_proto_v1_B.log
  Score: 75.0%
  ✓ total_requests      actual=2468          expected=2468
  ✗ error_rate          actual=0.35          expected=0.39
  ✓ avg_rtt_ms          actual=51.7          expected=51.7
  ✓ top_congestion      actual=cubic         expected=cubic
  Points earned: 18.8 / 25

...

======================================================================
FINAL SCORE (Correctness): 58.8 / 70
======================================================================

Note: This score only covers correctness (70% of total grade).
Additional points for:
  - Robustness & extensibility: 15 points (manual review)
  - Code quality & documentation: 15 points (manual review)
```

### Scoring Breakdown

**Automated (70 points):**
- Dataset A correct: 20 points
- Dataset B correct: 25 points
- Dataset C correct: 25 points

**Manual Review (30 points):**
- Robustness & extensibility: 15 points
  - Handles bad lines gracefully
  - Warns about invalid data
  - Extensible design (strategy pattern, plugins, etc.)
- Code quality & documentation: 15 points
  - Clear code structure
  - AI usage documentation (prompts + explanations)
  - Good README with setup instructions

### Troubleshooting

**"Could not find executable program"**
- The grader looks for:
  - Python: `edge_proto_tool/main.py`, `src/edge_proto_tool/main.py`
  - Go: `edge_proto_tool`, `main`, `bin/edge_proto_tool`
- Ask the candidate to follow the directory structure in the README

**"Program timed out"**
- Default timeout is 30 seconds per dataset
- Check if the program has an infinite loop or is very inefficient

**"JSON parse error"**
- The program must output valid JSON to stdout
- Check if there's extra text before/after the JSON

---

## Frontend Challenge Grading

### Preparation

The frontend grader uses Playwright to test the candidate's React application.

**One-time setup:**
```bash
cd grading/frontend_dashboard
npm install
npx playwright install chromium
```

### Grading a Submission

**Important:** The candidate's app must be running before grading!

#### Step 1: Start the candidate's application

```bash
cd /path/to/candidate/submission
npm install
npm start
```

Verify it's running at `http://localhost:3000` (or note the actual port).

#### Step 2: Run the grader

```bash
cd grading/frontend_dashboard
./run_grader.sh /path/to/candidate/submission 3000
```

The second parameter is the port (default: 3000).

### What the Grader Tests

The Playwright test suite automatically verifies:

1. **Basic Metrics (20 points)**
   - Average latency calculation
   - Max latency calculation

2. **Alert Behavior (15 points)**
   - Alert shows when max > threshold
   - Alert hides when max < threshold

3. **Chart Rendering (15 points)**
   - Chart container exists with `data-testid="chart"`
   - Child element count = data point count

4. **Polling Interval (15 points)**
   - Requests occur every 5 seconds (±0.5s)

5. **Threshold Configuration (20 points)**
   - Default threshold (300) saved to localStorage
   - Threshold can be changed via input
   - Changes persist across page reloads
   - Threshold line visible in chart
   - Points above threshold are highlighted

6. **Historical Data (10 points)**
   - Retains last 10 minutes of data

7. **Error Handling (5 points)**
   - Shows error message on API failure
   - Continues polling after error

### Understanding the Output

```
==========================================
Frontend Dashboard - Auto Grader
==========================================

Submission directory: /path/to/submission
Candidate app URL: http://localhost:3000
Mock API URL: http://localhost:3001

Starting mock API server on port 3001...
✓ Mock API server running (PID: 12345)

Checking if candidate's app is running on port 3000...
✓ Candidate's app is running

Running automated tests...

Running 14 tests using 1 worker
  ✓ should display correct average latency (2s)
  ✓ should display correct max latency (2s)
  ✓ should show alert when max latency exceeds threshold (3s)
  ✓ should NOT show alert when max latency is below threshold (3s)
  ✓ should render chart with correct number of data points (2s)
  ✓ should poll API every 5 seconds (16s)
  ✓ should initialize with default threshold in localStorage (1s)
  ✓ should allow threshold adjustment and persist to localStorage (2s)
  ✗ should show threshold line in chart (2s)
  ✓ should highlight data points above threshold (2s)
  ✓ should persist threshold across page reloads (3s)
  ✓ should retain data from last 10 minutes (8s)
  ✓ should display error message when API fails (2s)
  ✓ should continue polling after API failure (7s)

==========================================
Calculating score...
==========================================
✓ should display correct average latency: +10 points
✓ should display correct max latency: +10 points
✓ should show alert when max latency exceeds threshold: +7.5 points
✓ should NOT show alert when max latency is below threshold: +7.5 points
✓ should render chart with correct number of data points: +15 points
✓ should poll API every 5 seconds: +15 points
✓ should initialize with default threshold in localStorage: +4 points
✓ should allow threshold adjustment and persist to localStorage: +4 points
✗ should show threshold line in chart: 0/4 points
✓ should highlight data points above threshold: +4 points
✓ should persist threshold across page reloads: +4 points
✓ should retain data from last 10 minutes: +10 points
✓ should display error message when API fails: +2.5 points
✓ should continue polling after API failure: +2.5 points

======================================================================
FINAL SCORE: 96.0 / 100
======================================================================
```

### Viewing Detailed Test Reports

After grading, detailed reports are available:

```bash
cd grading/frontend_dashboard
npx playwright show-report
```

This opens a browser with:
- Screenshots of failures
- Step-by-step execution traces
- Network activity logs
- Console output

### Troubleshooting

**"Candidate's app is not running"**
- Ensure the candidate started their dev server
- Check if it's on the expected port
- Try accessing it in a browser first

**"Error: page.locator: Timeout ... waiting for locator"**
- The required `data-testid` attribute is missing
- Check candidate's code for the required DOM structure
- Common issue: using `id` or `className` instead of `data-testid`

**"Mock API server failed to start"**
- Port 3001 might be in use
- Kill any existing process on that port: `lsof -ti:3001 | xargs kill`

**Tests are flaky (sometimes pass, sometimes fail)**
- Network timing issues
- Try running again
- Check if the candidate's app has race conditions

---

## Batch Grading Multiple Submissions

### Backend

```bash
cd grading/edge_proto

# Grade all submissions in a directory
for submission in /path/to/submissions/*; do
    echo "Grading: $submission"
    ./run_grader.sh "$submission" > "results/$(basename $submission).txt" 2>&1
done
```

### Frontend

**Note:** Frontend grading requires each candidate's app to be started manually. Consider:

1. **Sequential approach**: Grade one at a time
2. **Port allocation**: Assign different ports to each candidate
3. **Automated start**: Create a script that `cd`s and runs `npm start` for each submission

Example:
```bash
# Start candidate's app in background
cd /path/to/candidate/submission
npm install
PORT=3000 npm start &
APP_PID=$!

# Wait for app to start
sleep 5

# Grade
cd /path/to/grading/frontend_dashboard
./run_grader.sh /path/to/candidate/submission 3000 > results.txt

# Stop app
kill $APP_PID
```

---

## Answering the Exam Admin's Questions

### For Backend (edge-proto-challenge):

**Q: 需要您再完善一下评分标准的细节**

✅ **Answer:** We've implemented fully automated grading:
- Clear API specification in the README (section 二)
- Command line interface: `python -m edge_proto_tool.main <input_file>`
- Exact JSON output format required
- Automated comparison against ground truth
- 70 points automatically scored, 30 points manual review

**Q: 看看您这里有没有什么其他的比较容易做自定评分的方式**

✅ **Answer:** The current approach is the easiest:
- Candidates output JSON to stdout
- Grader compares JSON fields with tolerance
- No need for candidates to follow specific class names or function signatures
- Just run their program and check the output

**Q: 如果用接口的方式来验证的话，就需要更明确一些的接口名称和格式**

✅ **Answer:** Done! The README now includes (section 二):
- Exact command format
- Required JSON fields and types
- Format requirements (decimal places)
- Error handling requirements (warnings to stderr)
- Example commands

### For Frontend (frontend-live-latency-dashboard):

**Q: 前端是用自动化测试吗？需要提前搭测试框架吗？**

✅ **Answer:** Yes, we recommend automated testing:
- We've provided a complete Playwright test suite
- Mock API server included
- Tests all requirements programmatically
- Candidates don't need to set up testing themselves

**Q: 前端开发人数不多，之前考虑搭框架比较复杂，我们就打算人工验证**

✅ **Answer:** Automated testing is actually simpler for grading:
- Framework is already set up in `grading/frontend_dashboard/`
- Just run `./run_grader.sh <submission>`
- Takes 2-3 minutes vs 15-20 minutes manual
- More consistent and objective

**Q: 您再看一下，现在的功能描述、如果人工验证的话，是否足够清晰**

✅ **Answer:** The README is now very clear:
- Exact DOM structure required with `data-testid` attributes
- Precise requirements for each feature
- Test criteria listed with point values
- Candidates can verify locally using browser DevTools

**Q: 除了直接看页面，是否也需要配合开发者工具来确认**

✅ **Answer:** Manual verification would require DevTools to check:
- localStorage persistence
- Network polling interval
- Chart child element count
- Error states

But with automated testing, this is all verified programmatically!

---

## Best Practices

### DO:
- Run graders on the same machine/environment for consistency
- Review manual components (code quality, documentation) separately
- Keep candidate submissions in separate directories
- Test the grading system yourself before actual grading

### DON'T:
- Modify the expected results without good reason
- Grade partial/incomplete submissions (ask candidates to fix first)
- Change tolerance values without documenting why
- Skip the automated tests and grade manually

---

## Support

If you encounter issues:

1. Check this guide's Troubleshooting sections
2. Verify setup: Python version, Node version, dependencies
3. Test with a known-good reference implementation
4. Check file permissions on scripts

For technical questions, refer to:
- `GRADING_STRATEGY.md` - Overall strategy and design decisions
- README files in each challenge - Candidate-facing specifications
- Source code comments in grading scripts

---

## Summary

**Backend Grading:**
```bash
cd grading/edge_proto
./run_grader.sh /path/to/submission
```

**Frontend Grading:**
```bash
# Terminal 1: Start candidate's app
cd /path/to/submission && npm install && npm start

# Terminal 2: Run grader
cd grading/frontend_dashboard
./run_grader.sh /path/to/submission 3000
```

Both systems provide objective, reproducible, and fair grading. Good luck!
