#!/bin/bash
#
# Edge-Proto Challenge - Exam Grading Script
#
# This script grades a student submission in one command.
#
# Usage:
#   ./run_exam.sh <submission_directory>
#
# Example:
#   ./run_exam.sh /exam/submissions/student_001
#
# Output:
#   - Console: Summary with score and grade
#   - File: Detailed JSON report in results/
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script directory (where this script and test data live)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
HIDDEN_DATA_DIR="${SCRIPT_DIR}/hidden_data"
EXPECTED_FILE="${SCRIPT_DIR}/expected_results.json"

# Validate arguments
if [ "$#" -lt 1 ]; then
    echo -e "${RED}Error: Missing submission directory${NC}"
    echo ""
    echo "Usage: $0 <submission_directory>"
    echo ""
    echo "Example:"
    echo "  $0 /exam/submissions/student_001"
    exit 1
fi

SUBMISSION_DIR="$(realpath "$1")"
STUDENT_ID="$(basename "$SUBMISSION_DIR")"

# Validate submission directory
if [ ! -d "$SUBMISSION_DIR" ]; then
    echo -e "${RED}Error: Submission directory not found: $SUBMISSION_DIR${NC}"
    exit 1
fi

# Validate hidden data
if [ ! -d "$HIDDEN_DATA_DIR" ]; then
    echo -e "${RED}Error: Hidden data directory not found: $HIDDEN_DATA_DIR${NC}"
    echo "Please ensure hidden_data/ directory exists with test files."
    exit 1
fi

if [ ! -f "$EXPECTED_FILE" ]; then
    echo -e "${RED}Error: Expected results file not found: $EXPECTED_FILE${NC}"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="${RESULTS_DIR}/${STUDENT_ID}_${TIMESTAMP}.json"

echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}  Edge-Proto Challenge - Auto Grader${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""
echo -e "Student ID:  ${BLUE}${STUDENT_ID}${NC}"
echo -e "Submission:  ${SUBMISSION_DIR}"
echo -e "Timestamp:   $(date)"
echo ""

# Run the grader
echo -e "${YELLOW}Running grader...${NC}"
echo ""

python3 "${SCRIPT_DIR}/grader.py" \
    --submission "$SUBMISSION_DIR" \
    --hidden-data "$HIDDEN_DATA_DIR" \
    --expected "$EXPECTED_FILE" \
    --output "$RESULT_FILE"

GRADE_EXIT_CODE=$?

echo ""
echo -e "Detailed report saved to: ${BLUE}${RESULT_FILE}${NC}"
echo ""

exit $GRADE_EXIT_CODE
