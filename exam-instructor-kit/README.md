# Exam Instructor Kit

Unified grading system for coding challenges.

## Directory Structure

```
exam-instructor-kit/
├── README.md                  # This file
├── grading_server.py          # Unified HTTP grading server
├── .api_key                   # API key (auto-generated)
├── grading_results.db         # SQLite database (auto-created)
│
├── edge-proto/                # Backend challenge
│   ├── grader.py              # Core grading logic
│   ├── run_exam.sh            # Grade single submission
│   ├── batch_grade.sh         # Grade all submissions
│   ├── expected_results.json  # Answer key
│   ├── hidden_data/           # Test datasets
│   └── README.md
│
└── frontend-dashboard/        # Frontend challenge
    ├── grader.spec.js         # Playwright tests
    ├── playwright.config.js
    ├── mock-api-server.js
    ├── package.json
    └── README.md
```

---

## Quick Start

### Option 1: Online Grading Server (Recommended)

Start the unified server that handles both challenges:

```bash
# Start server
python grading_server.py --port 8123

# Access web UI
open http://localhost:8123
```

Submit via API:
```bash
# Edge-Proto challenge
curl -X POST http://localhost:8123/submit \
  -H "X-API-Key: your-api-key" \
  -H "X-Student-ID: student_001" \
  -H "X-Challenge: edge-proto" \
  -F "submission=@submission.zip"

# Frontend challenge
curl -X POST http://localhost:8123/submit \
  -H "X-API-Key: your-api-key" \
  -H "X-Student-ID: student_001" \
  -H "X-Challenge: frontend" \
  -F "submission=@submission.zip"
```

### Option 2: Local Grading (Edge-Proto Only)

```bash
# Single submission
./edge-proto/run_exam.sh /path/to/submission/

# Batch grading
./edge-proto/batch_grade.sh /path/to/submissions/
```

---

## Challenges

### Edge-Proto (Backend)

**Type:** Log parsing (Python/Go)

**Scoring:**
| Dataset | Points |
|---------|--------|
| A (v1.0 normal) | 20 |
| B (v1.0 errors) | 30 |
| C (v1.1 extended) | 36 |
| D (robustness) | 14 |
| **Total** | **100** |

**Pass threshold:** 60 points

### Frontend Dashboard

**Type:** React application with Playwright testing

**Scoring:**
| Category | Points |
|----------|--------|
| Basic Metrics | 20 |
| Alert Behavior | 15 |
| Chart Rendering | 15 |
| Polling Interval | 15 |
| Threshold Config | 20 |
| Historical Data | 10 |
| Error Handling | 5 |
| **Total** | **100** |

**Pass threshold:** 60 points

---

## Grading Server API

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | No | Web UI |
| GET | /health | No | Health check |
| GET | /status | No | Statistics |
| GET | /results | Yes | All results |
| GET | /results/:id | Yes | Student results |
| POST | /submit | Yes | Submit for grading |

### Submit Headers

```
X-API-Key: <api_key>            # Required
X-Student-ID: <student_id>      # Required
X-Challenge: edge-proto|frontend # Required
```

### Example Response

```json
{
  "success": true,
  "student_id": "student_001",
  "challenge": "edge-proto",
  "timestamp": "2024-01-15T10:30:00",
  "result": {
    "total_score": 86,
    "max_score": 100,
    "grade": "B",
    "passed": true
  }
}
```

---

## First-Time Setup

### 1. Generate API Key

```bash
python grading_server.py --generate-key
```

Save the generated key - you'll need to share it with authorized users.

### 2. Install Frontend Dependencies (if using frontend challenge)

```bash
cd frontend-dashboard
npm install
npx playwright install chromium
```

### 3. Start Server

```bash
python grading_server.py --port 8123
```

---

## Grade Scale

| Score | Grade |
|-------|-------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| <60 | F |

---

## Database

All submissions are stored in SQLite (`grading_results.db`).

Export to CSV:
```bash
sqlite3 -header -csv grading_results.db \
  "SELECT student_id, challenge, total_score, grade, passed, timestamp
   FROM submissions ORDER BY timestamp DESC" > results.csv
```

---

## Security Features

### Sandbox Protection

The grading server includes multiple layers of security:

1. **Code Scanning** - Before execution, submissions are scanned for dangerous patterns:
   - Destructive commands: `rm -rf`, `dd`, `mkfs`
   - System modification: writes to `/etc`, `/usr`, `/bin`
   - Fork bombs and resource exhaustion
   - Network attacks: reverse shells, remote code execution
   - Privilege escalation: `sudo`, `su`, setuid
   - Crypto mining indicators

2. **Resource Limits** - Student code runs with strict limits:
   - CPU time: 30-60 seconds
   - Memory: 256-512 MB
   - File size: 10-50 MB
   - Process count: 10-50
   - Open files: 256

3. **Environment Sanitization** - Minimal PATH, no dangerous environment variables

4. **Optional Container Sandbox** - If `firejail` or `bubblewrap` is installed:
   - Network isolation (no network access for backend challenge)
   - Filesystem isolation (read-only system paths)
   - PID namespace isolation

### Installing Enhanced Sandbox (Optional)

```bash
# Ubuntu/Debian - Firejail (recommended)
sudo apt install firejail

# Or Bubblewrap (lighter weight)
sudo apt install bubblewrap
```

The server auto-detects available tools on startup.

## Security Checklist

- [ ] API key file (`.api_key`) has restricted permissions (600)
- [ ] Hidden test data is not accessible to students
- [ ] Server is behind firewall/VPN if on public internet
- [ ] Rate limiting is enabled (10 requests/minute/IP)
- [ ] Database file is backed up regularly
- [ ] Consider installing `firejail` for enhanced sandboxing

---

## Troubleshooting

### "Could not find executable"
- Edge-proto: Check for `edge_proto_tool/main.py` or compiled binary
- Frontend: Check for `package.json` with `start` script

### "Timeout"
- Edge-proto: Student code may have infinite loop
- Frontend: Student app may be slow to start/respond

### "Node.js not installed"
- Frontend grading requires Node.js 16+
- Install: `sudo apt install nodejs npm`

### API Key Issues
```bash
# Regenerate key
python grading_server.py --generate-key
```

---

## Support

See individual challenge README files for detailed grading criteria and troubleshooting.
