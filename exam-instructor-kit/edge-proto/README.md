# Edge-Proto Challenge - Instructor Kit

## Overview

This kit contains everything needed to grade student submissions for the Edge-Proto log parsing challenge.

```
exam-instructor-kit/edge-proto/
├── README.md              # This file
├── run_exam.sh           # Grade single submission
├── batch_grade.sh        # Grade all submissions at once
├── grader.py             # Core grading logic
├── expected_results.json # Answer key
├── hidden_data/          # Test datasets (DO NOT share with students)
│   ├── edge_proto_v1_A.log
│   ├── edge_proto_v1_B.log
│   ├── edge_proto_v1_1_C.log
│   └── edge_proto_v1_1_D.log
└── results/              # Generated reports (created automatically)
```

## Quick Start

### Grade a Single Submission

```bash
./run_exam.sh /path/to/student_submission/
```

### Grade All Submissions (Batch)

```bash
./batch_grade.sh /path/to/submissions/
```

Output:
- Individual JSON reports in `results/`
- Summary CSV: `results/summary_YYYYMMDD_HHMMSS.csv`

---

## Scoring

| Dataset | Points | Description |
|---------|--------|-------------|
| A (v1.0 normal) | 20 | Basic log parsing |
| B (v1.0 errors) | 30 | Error handling + bad lines |
| C (v1.1 extended) | 36 | v1.1 format support |
| D (robustness) | 14 | All bad lines (should return 0) |
| **Total** | **100** | |

**Pass threshold: 60 points**

### Grading Rules

**Datasets A/B/C:**
- 4 fields, each worth 25% of dataset points
- `error_rate`: ±0.01 tolerance
- `avg_rtt_ms`: ±0.5 tolerance
- Others: exact match

**Dataset D:**
- Only checks `total_requests`
- Expected value: 0 (all lines are bad)
- Each incorrectly accepted line = -1 point

### Grade Scale

| Score | Grade |
|-------|-------|
| 90-100 | A |
| 80-89 | B |
| 70-79 | C |
| 60-69 | D |
| <60 | F |

---

## Exam Setup

### 1. Prepare Student Environment

Give students access to:
```
edge-proto-challenge/
├── README.md              # Challenge description
├── Dockerfile             # Development environment
├── docker-compose.yml
└── data/sample/           # Sample data only!
    ├── edge_proto_v1_A.log
    ├── edge_proto_v1_B.log
    ├── edge_proto_v1_1_C.log
    ├── edge_proto_v1_1_D.log
    └── expected_answers.json
```

**⚠️ DO NOT give students access to:**
- `data/hidden/` directory
- `exam-instructor-kit/` directory
- `grading/` directory

### 2. Student Submission Structure

Students should submit:
```
student_001/
├── edge_proto_tool/
│   ├── __init__.py
│   ├── main.py
│   └── parser.py
├── requirements.txt
└── README.md
```

Or for Go:
```
student_001/
├── edge_proto_tool    # compiled binary
├── main.go
├── parser.go
└── README.md
```

### 3. Grading Workflow

```
┌─────────────────────────────────────────────────────────┐
│  EXAM GRADING WORKFLOW                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Collect submissions                                 │
│     /exam/submissions/                                  │
│       ├── student_001/                                  │
│       ├── student_002/                                  │
│       └── ...                                           │
│                                                         │
│  2. Run batch grading                                   │
│     $ ./batch_grade.sh /exam/submissions/               │
│                                                         │
│  3. Review results                                      │
│     - Summary: results/summary_*.csv                    │
│     - Details: results/<student>_*.json                 │
│                                                         │
│  4. Export grades                                       │
│     - CSV can be imported to spreadsheet/LMS            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Docker-Based Grading (Recommended)

For consistent grading environment:

```bash
# Build grading container
docker build -t edge-proto-grader -f Dockerfile.grader .

# Grade single submission
docker run --rm \
  -v /path/to/submissions:/submissions:ro \
  -v $(pwd)/results:/results \
  edge-proto-grader \
  /submissions/student_001

# Batch grade
docker run --rm \
  -v /path/to/submissions:/submissions:ro \
  -v $(pwd)/results:/results \
  edge-proto-grader \
  --batch /submissions
```

---

## Troubleshooting

### "Could not find executable"

Student's submission is missing `edge_proto_tool/main.py` or compiled binary.

**Solution:** Check submission structure, may need manual review.

### "Program failed to execute"

Student's code has syntax errors or missing dependencies.

**Solution:** Try running manually:
```bash
cd /path/to/student_submission
python3 -m edge_proto_tool.main /path/to/test_file.log
```

### Inconsistent Results

Environment differences between student dev and grading.

**Solution:** Use Docker for both development and grading.

---

## Security Checklist

- [ ] Hidden test data is NOT in student-accessible repository
- [ ] `expected_results.json` is NOT shared with students
- [ ] Grading scripts are only on instructor machine
- [ ] Student Docker image only includes sample data
- [ ] Results directory has appropriate permissions

---

## Support

For issues with the grading system, check:
1. Python 3.8+ is installed
2. All hidden data files exist
3. Submission follows expected structure
