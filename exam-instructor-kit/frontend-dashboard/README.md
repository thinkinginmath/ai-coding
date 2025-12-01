# Frontend Dashboard Challenge - Instructor Kit

## Overview

This kit contains the grading system for the Frontend Live Latency Dashboard challenge.

```
frontend-dashboard/
├── README.md              # This file
├── grader.spec.js         # Playwright test suite (14 tests)
├── playwright.config.js   # Playwright configuration
├── mock-api-server.js     # Mock API for testing
├── package.json           # Node.js dependencies
└── run_grader.sh          # Manual grading script
```

## Scoring

| Category | Tests | Points |
|----------|-------|--------|
| Basic Metrics | 2 | 20 |
| Alert Behavior | 2 | 15 |
| Chart Rendering | 1 | 15 |
| Polling Interval | 1 | 15 |
| Threshold Config | 5 | 20 |
| Historical Data | 1 | 10 |
| Error Handling | 2 | 5 |
| **Total** | **14** | **100** |

**Pass threshold: 60 points**

### Test Details

| Test | Points |
|------|--------|
| should display correct average latency | 10 |
| should display correct max latency | 10 |
| should show alert when max latency exceeds threshold | 7.5 |
| should NOT show alert when max latency is below threshold | 7.5 |
| should render chart with correct number of data points | 15 |
| should poll API every 5 seconds | 15 |
| should initialize with default threshold in localStorage | 4 |
| should allow threshold adjustment and persist to localStorage | 4 |
| should show threshold line in chart | 4 |
| should highlight data points above threshold | 4 |
| should persist threshold across page reloads | 4 |
| should retain data from last 10 minutes | 10 |
| should display error message when API fails | 2.5 |
| should continue polling after API failure | 2.5 |

---

## Manual Grading

### Prerequisites

- Node.js 16+ installed
- npm installed

### Setup

```bash
# Install dependencies (first time)
npm install
npx playwright install chromium
```

### Grading a Submission

1. **Start the mock API server:**
```bash
node mock-api-server.js --mode=test --port=3001
```

2. **Start the student's app (in another terminal):**
```bash
cd /path/to/student/submission
npm install
npm start
# App should run on port 3000
```

3. **Run the grader:**
```bash
APP_URL=http://localhost:3000 API_URL=http://localhost:3001 npx playwright test
```

### Using the Helper Script

```bash
./run_grader.sh /path/to/student/submission 3000
```

Note: The student's app must already be running on the specified port.

---

## Online Grading

Use the unified grading server (see parent directory):

```bash
cd /path/to/exam-instructor-kit
python grading_server.py --port 8123

# Submit via curl
curl -X POST http://localhost:8123/submit \
  -H "X-API-Key: your-api-key" \
  -H "X-Student-ID: student_001" \
  -H "X-Challenge: frontend" \
  -F "submission=@student_submission.zip"
```

The online grader will:
1. Extract the ZIP
2. Install student's dependencies
3. Start the mock API and student's app
4. Run Playwright tests
5. Calculate and return the score

---

## Student Submission Requirements

Students must submit a React project with:

```
submission/
├── package.json          # With "start" script
├── src/
│   └── ... React components
└── ...
```

### Required DOM Elements

The student's app must include these `data-testid` attributes:

```html
<div data-testid="avg-latency">150.5</div>
<div data-testid="max-latency">305</div>
<input data-testid="threshold-input" type="number" />
<div data-testid="chart">...</div>
<div data-testid="alert">Latency spike detected</div> <!-- conditional -->
```

---

## Troubleshooting

### "App failed to start"

- Check if `npm start` script exists in package.json
- Check for syntax errors in student code
- Verify port 3000 is available

### "Tests timeout"

- Student app may be slow to render
- Check if student app is correctly polling the API
- Increase timeout in playwright.config.js if needed

### "Playwright not found"

```bash
npm install
npx playwright install chromium
```

---

## Security Notes

- Student code runs in a subprocess
- The grading server kills processes after timeout
- Submissions are extracted to temp directories and cleaned up
- Rate limiting prevents abuse
