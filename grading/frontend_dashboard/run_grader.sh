#!/bin/bash
# Automated grading script for frontend-live-latency-dashboard

set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: ./run_grader.sh <submission_directory> [candidate_port]"
    echo ""
    echo "Example:"
    echo "  ./run_grader.sh ../../submissions/candidate_001/ 3000"
    echo ""
    echo "The candidate's frontend should be running on the specified port (default: 3000)"
    exit 1
fi

SUBMISSION_DIR="$1"
CANDIDATE_PORT="${2:-3000}"
MOCK_API_PORT=3001
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Frontend Dashboard - Auto Grader"
echo "=========================================="
echo ""
echo "Submission directory: $SUBMISSION_DIR"
echo "Candidate app URL: http://localhost:$CANDIDATE_PORT"
echo "Mock API URL: http://localhost:$MOCK_API_PORT"
echo ""

# Check if submission directory exists
if [ ! -d "$SUBMISSION_DIR" ]; then
    echo "Error: Submission directory not found: $SUBMISSION_DIR"
    exit 1
fi

# Check if playwright is installed
if ! command -v npx &> /dev/null; then
    echo "Error: npm/npx not found. Please install Node.js"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "Installing dependencies..."
    cd "$SCRIPT_DIR"
    npm install
    npx playwright install chromium
    echo ""
fi

# Start mock API server in background
echo "Starting mock API server on port $MOCK_API_PORT..."
node "$SCRIPT_DIR/mock-api-server.js" --mode=test --port=$MOCK_API_PORT &
MOCK_PID=$!

# Give the server time to start
sleep 2

# Check if mock API is running
if ! curl -s "http://localhost:$MOCK_API_PORT/health" > /dev/null; then
    echo "Error: Mock API server failed to start"
    kill $MOCK_PID 2>/dev/null || true
    exit 1
fi

echo "✓ Mock API server running (PID: $MOCK_PID)"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping mock API server..."
    kill $MOCK_PID 2>/dev/null || true
    wait $MOCK_PID 2>/dev/null || true
}

trap cleanup EXIT

# Check if candidate's app is running
echo "Checking if candidate's app is running on port $CANDIDATE_PORT..."
if ! curl -s "http://localhost:$CANDIDATE_PORT" > /dev/null; then
    echo ""
    echo "=========================================="
    echo "WARNING: Candidate's app is not running!"
    echo "=========================================="
    echo ""
    echo "Please start the candidate's frontend application first:"
    echo "  cd $SUBMISSION_DIR"
    echo "  npm install"
    echo "  npm start"
    echo ""
    echo "Then run this grader again."
    exit 1
fi

echo "✓ Candidate's app is running"
echo ""

# Run Playwright tests
echo "Running automated tests..."
echo ""

cd "$SCRIPT_DIR"
APP_URL="http://localhost:$CANDIDATE_PORT" \
API_URL="http://localhost:$MOCK_API_PORT" \
npx playwright test

# Calculate score from results
if [ -f "test-results.json" ]; then
    echo ""
    echo "=========================================="
    echo "Calculating score..."
    echo "=========================================="

    # Parse test results and calculate score
    python3 - <<'EOF'
import json
import sys

try:
    with open('test-results.json', 'r') as f:
        results = json.load(f)

    # Test scoring map
    test_scores = {
        'should display correct average latency': 10,
        'should display correct max latency': 10,
        'should show alert when max latency exceeds threshold': 7.5,
        'should NOT show alert when max latency is below threshold': 7.5,
        'should render chart with correct number of data points': 15,
        'should poll API every 5 seconds': 15,
        'should initialize with default threshold in localStorage': 4,
        'should allow threshold adjustment and persist to localStorage': 4,
        'should show threshold line in chart': 4,
        'should highlight data points above threshold': 4,
        'should persist threshold across page reloads': 4,
        'should retain data from last 10 minutes': 10,
        'should display error message when API fails': 2.5,
        'should continue polling after API failure': 2.5,
    }

    total_score = 0
    max_score = 100

    if 'suites' in results:
        for suite in results['suites']:
            if 'specs' in suite:
                for spec in suite['specs']:
                    test_title = spec.get('title', '')
                    test_ok = spec.get('ok', False)

                    if test_title in test_scores:
                        points = test_scores[test_title]
                        if test_ok:
                            total_score += points
                            print(f"✓ {test_title}: +{points} points")
                        else:
                            print(f"✗ {test_title}: 0/{points} points")

    print("")
    print("=" * 70)
    print(f"FINAL SCORE: {total_score:.1f} / {max_score}")
    print("=" * 70)

except Exception as e:
    print(f"Error calculating score: {e}")
    sys.exit(1)
EOF
fi

echo ""
echo "=========================================="
echo "Grading complete!"
echo "=========================================="
echo ""
echo "Test report available at: playwright-report/index.html"
echo "To view: npx playwright show-report"
