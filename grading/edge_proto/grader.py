#!/usr/bin/env python3
"""
Auto-grader for edge-proto-challenge.

This script runs a candidate's submission against hidden test data and
compares the output against expected results.

Scoring:
- Dataset A (v1.0 normal): 20 points
- Dataset B (v1.0 with errors): 30 points
- Dataset C (v1.1 extended): 36 points
- Dataset D (all bad lines): 14 points

Total: 100 points
Pass threshold: 60 points

Usage:
    python grader.py <submission_dir>

Example:
    python grader.py ../../submissions/candidate_123/
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def find_executable(submission_dir: Path) -> Optional[Tuple[str, List[str]]]:
    """
    Detect how to run the candidate's program.

    Returns:
        (language, command_parts) or None if not found

    Supported patterns:
        Python: edge_proto_tool/main.py or src/edge_proto_tool/main.py
        Go: compiled binary named 'edge_proto_tool' or 'main'
    """

    # Try Python module structure
    python_patterns = [
        submission_dir / 'edge_proto_tool' / 'main.py',
        submission_dir / 'src' / 'edge_proto_tool' / 'main.py',
        submission_dir / 'main.py',
    ]

    for py_file in python_patterns:
        if py_file.exists():
            # Determine the module path
            if 'edge_proto_tool' in str(py_file):
                return ('python', ['python3', '-m', 'edge_proto_tool.main'])
            else:
                return ('python', ['python3', str(py_file)])

    # Try Go binary
    go_patterns = [
        submission_dir / 'edge_proto_tool',
        submission_dir / 'main',
        submission_dir / 'bin' / 'edge_proto_tool',
    ]

    for go_binary in go_patterns:
        if go_binary.exists() and go_binary.is_file():
            return ('go', [str(go_binary)])

    return None


def run_candidate_program(
    command_parts: List[str],
    input_file: Path,
    working_dir: Path,
    timeout: int = 30
) -> Tuple[Optional[Dict], str, str]:
    """
    Run the candidate's program on an input file.

    Returns:
        (parsed_json, stdout, stderr)
        parsed_json is None if execution failed or output was invalid
    """

    try:
        # Run the program
        result = subprocess.run(
            command_parts + [str(input_file)],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            return None, stdout, stderr

        # Try to parse JSON from stdout
        try:
            parsed = json.loads(stdout)
            return parsed, stdout, stderr
        except json.JSONDecodeError as e:
            return None, stdout, f"{stderr}\nJSON parse error: {str(e)}"

    except subprocess.TimeoutExpired:
        return None, "", f"Program timed out after {timeout} seconds"
    except Exception as e:
        return None, "", f"Execution error: {str(e)}"


def compare_results(
    actual: Dict,
    expected: Dict,
    tolerance: Dict[str, float] = None
) -> Tuple[float, Dict[str, bool]]:
    """
    Compare actual output against expected results.

    Returns:
        (score_percentage, field_results)

    tolerance: dict of field_name -> max_acceptable_difference
    """

    if tolerance is None:
        tolerance = {
            'error_rate': 0.01,    # ±0.01
            'avg_rtt_ms': 0.5,     # ±0.5ms
        }

    field_results = {}
    total_fields = 4
    correct_fields = 0

    # Check total_requests (exact match)
    if actual.get('total_requests') == expected.get('total_requests'):
        field_results['total_requests'] = True
        correct_fields += 1
    else:
        field_results['total_requests'] = False

    # Check error_rate (with tolerance)
    actual_er = actual.get('error_rate', -1)
    expected_er = expected.get('error_rate', -1)
    if abs(actual_er - expected_er) <= tolerance['error_rate']:
        field_results['error_rate'] = True
        correct_fields += 1
    else:
        field_results['error_rate'] = False

    # Check avg_rtt_ms (with tolerance)
    actual_rtt = actual.get('avg_rtt_ms', -1)
    expected_rtt = expected.get('avg_rtt_ms', -1)
    if abs(actual_rtt - expected_rtt) <= tolerance['avg_rtt_ms']:
        field_results['avg_rtt_ms'] = True
        correct_fields += 1
    else:
        field_results['avg_rtt_ms'] = False

    # Check top_congestion (exact match, or both empty)
    actual_tc = actual.get('top_congestion', '')
    expected_tc = expected.get('top_congestion', '')
    if actual_tc == expected_tc:
        field_results['top_congestion'] = True
        correct_fields += 1
    else:
        field_results['top_congestion'] = False

    score_percentage = (correct_fields / total_fields) * 100
    return score_percentage, field_results


def grade_dataset_d(actual: Dict, expected: Dict) -> Tuple[float, int]:
    """
    Special grading for Dataset D (all bad lines).

    Dataset D contains 14 bad lines. A correct implementation should
    return total_requests = 0.

    Each incorrectly counted line (total_requests > 0) results in 1 point deduction.

    Returns:
        (score, total_requests_value)
    """
    max_points = 14
    actual_total = actual.get('total_requests', 0)

    if actual_total == 0:
        return max_points, actual_total
    elif actual_total >= 14:
        return 0, actual_total
    else:
        return max_points - actual_total, actual_total


def print_test_result(
    dataset_name: str,
    success: bool,
    score: float,
    actual: Optional[Dict],
    expected: Dict,
    field_results: Optional[Dict[str, bool]],
    stderr: str,
    points: float,
    max_points: float,
    is_dataset_d: bool = False
):
    """Print a formatted test result."""

    print(f"\n{Colors.BOLD}Dataset: {dataset_name}{Colors.RESET}")

    if not success:
        print(f"  {Colors.RED}✗ FAILED - Program did not execute successfully{Colors.RESET}")
        if stderr:
            print(f"  Error output: {stderr[:200]}")
        print(f"  Points earned: 0 / {max_points}")
        return

    if is_dataset_d:
        # Special output for Dataset D
        actual_total = actual.get('total_requests', 0) if actual else -1
        if actual_total == 0:
            print(f"  {Colors.GREEN}✓ All bad lines correctly rejected{Colors.RESET}")
        else:
            print(f"  {Colors.RED}✗ total_requests = {actual_total} (should be 0){Colors.RESET}")
        print(f"  Points earned: {points:.1f} / {max_points}")
    else:
        print(f"  Score: {score:.1f}%")

        # Print field-by-field comparison
        fields = ['total_requests', 'error_rate', 'avg_rtt_ms', 'top_congestion']
        for field in fields:
            is_correct = field_results.get(field, False)
            status = f"{Colors.GREEN}✓{Colors.RESET}" if is_correct else f"{Colors.RED}✗{Colors.RESET}"

            actual_val = actual.get(field, 'N/A')
            expected_val = expected.get(field, 'N/A')

            print(f"  {status} {field:20s} actual={actual_val:<15} expected={expected_val}")

        print(f"  Points earned: {points:.1f} / {max_points}")

    # Check if warnings were produced for bad lines
    if stderr and 'warning' in stderr.lower():
        print(f"  {Colors.GREEN}✓{Colors.RESET} Program produced warnings for bad lines")


def main():
    """Main grading workflow."""

    if len(sys.argv) != 2:
        print("Usage: python grader.py <submission_dir>")
        sys.exit(1)

    submission_dir = Path(sys.argv[1]).resolve()

    if not submission_dir.exists():
        print(f"Error: Submission directory not found: {submission_dir}")
        sys.exit(1)

    print(f"{Colors.BOLD}Edge-Proto Challenge Auto-Grader{Colors.RESET}")
    print(f"Submission: {submission_dir.name}")
    print("=" * 70)
    print(f"\nScoring: A=20, B=30, C=36, D=14 (Total: 100, Pass: 60)")

    # Load expected results
    script_dir = Path(__file__).parent
    expected_file = script_dir / 'expected_results.json'

    if not expected_file.exists():
        print(f"Error: Expected results not found. Run generate_ground_truth.py first.")
        sys.exit(1)

    with open(expected_file, 'r') as f:
        expected_results = json.load(f)

    # Detect how to run the program
    executable_info = find_executable(submission_dir)

    if executable_info is None:
        print(f"{Colors.RED}Error: Could not find executable program in submission.{Colors.RESET}")
        print("\nLooked for:")
        print("  - Python: edge_proto_tool/main.py, src/edge_proto_tool/main.py")
        print("  - Go: edge_proto_tool, main, bin/edge_proto_tool")
        sys.exit(1)

    language, command_parts = executable_info
    print(f"\n{Colors.GREEN}✓{Colors.RESET} Detected {language} program: {' '.join(command_parts)}")

    # Locate hidden test data
    repo_root = script_dir.parent.parent
    hidden_data_dir = repo_root / 'edge-proto-challenge' / 'data' / 'hidden'

    if not hidden_data_dir.exists():
        print(f"Error: Hidden test data not found: {hidden_data_dir}")
        sys.exit(1)

    # Run tests - updated scoring
    datasets = [
        ('edge_proto_v1_A.log', 20, False),      # v1.0 normal traffic
        ('edge_proto_v1_B.log', 30, False),      # v1.0 with errors
        ('edge_proto_v1_1_C.log', 36, False),    # v1.1 extended
        ('edge_proto_v1_1_D.log', 14, True),     # all bad lines (robustness)
    ]

    total_score = 0
    max_score = 100

    for dataset_name, max_points, is_dataset_d in datasets:
        input_file = hidden_data_dir / dataset_name

        if dataset_name not in expected_results:
            print(f"\n{Colors.YELLOW}⚠ Skipping {dataset_name}: no expected results{Colors.RESET}")
            continue

        expected = expected_results[dataset_name]

        # Run the program
        result, stdout, stderr = run_candidate_program(
            command_parts,
            input_file,
            submission_dir
        )

        if result is None:
            print_test_result(
                dataset_name, False, 0, None, expected, None, stderr,
                0, max_points, is_dataset_d
            )
            continue

        if is_dataset_d:
            # Special grading for Dataset D
            points, actual_total = grade_dataset_d(result, expected)
            total_score += points
            print_test_result(
                dataset_name, True, 0, result, expected, None, stderr,
                points, max_points, True
            )
        else:
            # Normal grading for A/B/C
            score_pct, field_results = compare_results(result, expected)
            dataset_score = (score_pct / 100) * max_points
            total_score += dataset_score
            print_test_result(
                dataset_name, True, score_pct, result, expected, field_results, stderr,
                dataset_score, max_points, False
            )

    # Summary
    print("\n" + "=" * 70)
    passed = total_score >= 60
    status_color = Colors.GREEN if passed else Colors.RED
    status_text = "PASSED" if passed else "FAILED"

    print(f"{Colors.BOLD}FINAL SCORE: {total_score:.1f} / {max_score} ({status_color}{status_text}{Colors.RESET}){Colors.RESET}")
    print(f"\nPass threshold: 60 points")


if __name__ == '__main__':
    main()
