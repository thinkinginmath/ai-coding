#!/bin/bash
#
# Batch grade all submissions in a directory
#
# Usage:
#   ./batch_grade.sh <submissions_directory>
#
# Example:
#   ./batch_grade.sh /exam/submissions/
#
# This will grade all subdirectories and generate:
#   - Individual JSON reports in results/
#   - Summary CSV file: results/summary_YYYYMMDD_HHMMSS.csv
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
HIDDEN_DATA="${SCRIPT_DIR}/hidden_data"
EXPECTED="${SCRIPT_DIR}/expected_results.json"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <submissions_directory>"
    exit 1
fi

SUBMISSIONS_DIR="$(realpath "$1")"

if [ ! -d "$SUBMISSIONS_DIR" ]; then
    echo "Error: Submissions directory not found: $SUBMISSIONS_DIR"
    exit 1
fi

mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_FILE="${RESULTS_DIR}/summary_${TIMESTAMP}.csv"

# CSV Header
echo "student_id,total_score,grade,passed,dataset_a,dataset_b,dataset_c,dataset_d,timestamp" > "$SUMMARY_FILE"

echo ""
echo "=========================================="
echo "  Batch Grading - Edge-Proto Challenge"
echo "=========================================="
echo "Submissions: $SUBMISSIONS_DIR"
echo "Results: $RESULTS_DIR"
echo ""

# Count submissions
TOTAL=$(find "$SUBMISSIONS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
CURRENT=0
PASSED=0
FAILED=0

# Grade each submission
for submission in "$SUBMISSIONS_DIR"/*/; do
    if [ -d "$submission" ]; then
        CURRENT=$((CURRENT + 1))
        STUDENT_ID=$(basename "$submission")
        RESULT_FILE="${RESULTS_DIR}/${STUDENT_ID}_${TIMESTAMP}.json"

        echo "[$CURRENT/$TOTAL] Grading: $STUDENT_ID"

        # Run grader (suppress output, capture result)
        if python3 "${SCRIPT_DIR}/grader.py" \
            --submission "$submission" \
            --hidden-data "$HIDDEN_DATA" \
            --expected "$EXPECTED" \
            --output "$RESULT_FILE" > /dev/null 2>&1; then
            STATUS="PASSED"
            PASSED=$((PASSED + 1))
        else
            STATUS="FAILED"
            FAILED=$((FAILED + 1))
        fi

        # Extract scores from JSON for CSV
        if [ -f "$RESULT_FILE" ]; then
            SCORE=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); print(d['total_score'])")
            GRADE=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); print(d['grade'])")
            PASS=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); print('yes' if d['passed'] else 'no')")

            # Get per-dataset scores
            DS_A=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); ds=[x for x in d['datasets'] if 'A.log' in x['name']]; print(ds[0]['points_earned'] if ds else 0)")
            DS_B=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); ds=[x for x in d['datasets'] if 'B.log' in x['name']]; print(ds[0]['points_earned'] if ds else 0)")
            DS_C=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); ds=[x for x in d['datasets'] if 'C.log' in x['name']]; print(ds[0]['points_earned'] if ds else 0)")
            DS_D=$(python3 -c "import json; d=json.load(open('$RESULT_FILE')); ds=[x for x in d['datasets'] if 'D.log' in x['name']]; print(ds[0]['points_earned'] if ds else 0)")

            echo "${STUDENT_ID},${SCORE},${GRADE},${PASS},${DS_A},${DS_B},${DS_C},${DS_D},${TIMESTAMP}" >> "$SUMMARY_FILE"

            echo "         Score: $SCORE/100, Grade: $GRADE, $STATUS"
        else
            echo "${STUDENT_ID},0,F,no,0,0,0,0,${TIMESTAMP}" >> "$SUMMARY_FILE"
            echo "         ERROR: Could not grade"
        fi
    fi
done

echo ""
echo "=========================================="
echo "  BATCH GRADING COMPLETE"
echo "=========================================="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""
echo "Summary CSV: $SUMMARY_FILE"
echo "Individual reports: $RESULTS_DIR/"
echo ""
