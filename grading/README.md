# Auto-Grading System

This directory contains automated grading tools for the AI coding challenges.

## Quick Start

### Backend Challenge (edge-proto-challenge)

```bash
cd edge_proto

# One-time setup: generate expected results
python3 generate_ground_truth.py

# Grade a submission
./run_grader.sh /path/to/candidate/submission
```

### Frontend Challenge (frontend-live-latency-dashboard)

```bash
cd frontend_dashboard

# One-time setup: install dependencies
npm install
npx playwright install chromium

# Start the candidate's app first (in another terminal)
cd /path/to/candidate/submission
npm install && npm start

# Then run the grader
cd grading/frontend_dashboard
./run_grader.sh /path/to/candidate/submission 3000
```

## Documentation

- **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)** - Complete guide for instructors on how to use the grading system
- **[../GRADING_STRATEGY.md](../GRADING_STRATEGY.md)** - Overall strategy, design decisions, and scoring breakdown

## Directory Structure

```
grading/
├── README.md                    # This file
├── INSTRUCTOR_GUIDE.md          # Detailed instructor guide
│
├── edge_proto/                  # Backend challenge grading
│   ├── generate_ground_truth.py # Generate expected results
│   ├── grader.py                # Main grading script
│   ├── expected_results.json    # Ground truth data
│   └── run_grader.sh            # Convenience script
│
└── frontend_dashboard/          # Frontend challenge grading
    ├── mock-api-server.js       # Mock API for testing
    ├── grader.spec.js           # Playwright test suite
    ├── playwright.config.js     # Playwright configuration
    ├── package.json             # Dependencies
    └── run_grader.sh            # Convenience script
```

## Features

### Backend Grading
- ✅ Automatic program detection (Python/Go)
- ✅ Runs on hidden test datasets
- ✅ JSON output comparison with tolerance
- ✅ Detailed field-by-field scoring
- ✅ Checks for proper error handling

### Frontend Grading
- ✅ Automated DOM testing with Playwright
- ✅ Mock API server with controlled data
- ✅ Tests all requirements (metrics, alerts, charts, polling)
- ✅ Verifies localStorage persistence
- ✅ Checks error handling
- ✅ Generates detailed HTML reports

## Scoring

### Backend (70 points automated + 30 manual)
- Dataset A (v1.0 normal): 20 points
- Dataset B (v1.0 errors): 25 points
- Dataset C (v1.1 extended): 25 points
- Manual review: 30 points (robustness, code quality)

### Frontend (100 points automated)
- Basic metrics: 20 points
- Alert behavior: 15 points
- Chart rendering: 15 points
- Polling interval: 15 points
- Threshold config: 20 points
- Historical data: 10 points
- Error handling: 5 points

## Requirements

- Python 3.8+
- Node.js 16+
- npm
- Bash shell (Linux/macOS/WSL)

## Support

For detailed instructions, troubleshooting, and best practices, see [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md).
