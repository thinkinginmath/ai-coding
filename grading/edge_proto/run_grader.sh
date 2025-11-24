#!/bin/bash
# Automated grading script for edge-proto-challenge

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: ./run_grader.sh <submission_directory>"
    echo ""
    echo "Example:"
    echo "  ./run_grader.sh ../../submissions/candidate_001/"
    exit 1
fi

SUBMISSION_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Edge Proto Challenge - Auto Grader"
echo "=========================================="
echo ""
echo "Submission directory: $SUBMISSION_DIR"
echo ""

# Check if expected results exist
if [ ! -f "$SCRIPT_DIR/expected_results.json" ]; then
    echo "Error: expected_results.json not found!"
    echo "Please run generate_ground_truth.py first:"
    echo "  python3 $SCRIPT_DIR/generate_ground_truth.py"
    exit 1
fi

# Check if submission directory exists
if [ ! -d "$SUBMISSION_DIR" ]; then
    echo "Error: Submission directory not found: $SUBMISSION_DIR"
    exit 1
fi

# Run the grader
echo "Running grader..."
echo ""

python3 "$SCRIPT_DIR/grader.py" "$SUBMISSION_DIR"

echo ""
echo "=========================================="
echo "Grading complete!"
echo "=========================================="
