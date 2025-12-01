#!/usr/bin/env python3
"""
Edge-Proto Challenge - Standalone Grader

This grader is designed for exam execution with all paths configurable.

Usage:
    python grader.py --submission <dir> --hidden-data <dir> --expected <file> [--output <file>]

Scoring:
    - Dataset A (v1.0 normal): 20 points
    - Dataset B (v1.0 errors): 30 points
    - Dataset C (v1.1 extended): 36 points
    - Dataset D (all bad lines): 14 points
    Total: 100 points, Pass: 60 points
"""

import argparse
import json
import os
import resource
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


# =============================================================================
# Sandbox - Resource Limits for Student Code
# =============================================================================

SANDBOX_MAX_CPU_TIME = 30  # seconds
SANDBOX_MAX_MEMORY = 256 * 1024 * 1024  # 256 MB
SANDBOX_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SANDBOX_MAX_PROCESSES = 10


def set_resource_limits():
    """Set resource limits for student code execution."""
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (SANDBOX_MAX_CPU_TIME, SANDBOX_MAX_CPU_TIME))
        resource.setrlimit(resource.RLIMIT_AS, (SANDBOX_MAX_MEMORY, SANDBOX_MAX_MEMORY))
        resource.setrlimit(resource.RLIMIT_FSIZE, (SANDBOX_MAX_FILE_SIZE, SANDBOX_MAX_FILE_SIZE))
        resource.setrlimit(resource.RLIMIT_NPROC, (SANDBOX_MAX_PROCESSES, SANDBOX_MAX_PROCESSES))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))  # No core dumps
    except Exception:
        pass  # Best effort


def get_safe_environment() -> dict:
    """Get sanitized environment for running student code."""
    return {
        'PATH': '/usr/local/bin:/usr/bin:/bin',
        'HOME': '/tmp',
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONUNBUFFERED': '1',
    }


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FieldResult:
    field_name: str
    expected: Any
    actual: Any
    is_correct: bool
    points: float


@dataclass
class DatasetResult:
    name: str
    version: str
    category: str
    points_earned: float
    points_possible: float
    percentage: float
    fields: List[FieldResult]
    success: bool
    error_message: str


@dataclass
class GradingResult:
    student_id: str
    timestamp: str
    total_score: float
    max_score: float
    percentage: float
    grade: str
    passed: bool
    datasets: List[DatasetResult]
    summary: str


# =============================================================================
# Utility Functions
# =============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def calculate_grade(percentage: float) -> str:
    if percentage >= 90: return "A"
    elif percentage >= 80: return "B"
    elif percentage >= 70: return "C"
    elif percentage >= 60: return "D"
    else: return "F"


def find_executable(submission_dir: Path) -> Optional[Tuple[str, List[str]]]:
    """Detect how to run the student's program."""

    # Python patterns
    for pattern in [
        submission_dir / 'edge_proto_tool' / 'main.py',
        submission_dir / 'src' / 'edge_proto_tool' / 'main.py',
        submission_dir / 'main.py',
    ]:
        if pattern.exists():
            if 'edge_proto_tool' in str(pattern):
                return ('python', ['python3', '-m', 'edge_proto_tool.main'])
            return ('python', ['python3', str(pattern)])

    # Go patterns
    for pattern in [
        submission_dir / 'edge_proto_tool',
        submission_dir / 'main',
    ]:
        if pattern.exists() and pattern.is_file():
            # Check if executable
            try:
                if pattern.stat().st_mode & 0o111:
                    return ('go', [str(pattern)])
            except:
                pass

    return None


def run_program(
    command: List[str],
    input_file: Path,
    working_dir: Path,
    timeout: int = 30
) -> Tuple[Optional[Dict], str, str]:
    """Run student program and capture output with sandboxing."""

    try:
        result = subprocess.run(
            command + [str(input_file)],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=get_safe_environment(),
            preexec_fn=set_resource_limits  # Apply resource limits
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            # Check for resource limit signals
            if result.returncode == -9:  # SIGKILL (memory limit)
                return None, stdout, "Process killed (likely memory limit exceeded)"
            elif result.returncode == -24:  # SIGXCPU (CPU limit)
                return None, stdout, "CPU time limit exceeded"
            return None, stdout, f"Exit code {result.returncode}: {stderr}"

        try:
            parsed = json.loads(stdout)
            return parsed, stdout, stderr
        except json.JSONDecodeError as e:
            return None, stdout, f"Invalid JSON output: {e}"

    except subprocess.TimeoutExpired:
        return None, "", f"Timeout after {timeout}s"
    except Exception as e:
        return None, "", f"Execution error: {e}"


# =============================================================================
# Grading Logic
# =============================================================================

DATASETS = [
    # (filename, version, category, max_points)
    ('edge_proto_v1_A.log', 'v1.0', 'correctness', 20),
    ('edge_proto_v1_B.log', 'v1.0', 'correctness', 30),
    ('edge_proto_v1_1_C.log', 'v1.1', 'correctness', 36),
    ('edge_proto_v1_1_D.log', 'v1.1', 'robustness', 14),
]

TOLERANCE = {
    'error_rate': 0.01,
    'avg_rtt_ms': 0.5,
}


def grade_correctness(actual: Dict, expected: Dict, max_points: float) -> Tuple[float, List[FieldResult]]:
    """Grade a correctness dataset (A, B, C)."""

    fields = ['total_requests', 'error_rate', 'avg_rtt_ms', 'top_congestion']
    results = []
    correct = 0
    points_per_field = max_points / 4

    for field in fields:
        exp_val = expected.get(field)
        act_val = actual.get(field)

        if field in TOLERANCE:
            try:
                is_correct = abs(float(act_val or 0) - float(exp_val or 0)) <= TOLERANCE[field]
            except (TypeError, ValueError):
                is_correct = False
        else:
            is_correct = (act_val == exp_val)

        if is_correct:
            correct += 1

        results.append(FieldResult(
            field_name=field,
            expected=exp_val,
            actual=act_val,
            is_correct=is_correct,
            points=points_per_field if is_correct else 0
        ))

    total_points = (correct / 4) * max_points
    return total_points, results


def grade_robustness(actual: Dict, expected: Dict, max_points: float) -> Tuple[float, List[FieldResult]]:
    """Grade Dataset D (all bad lines)."""

    actual_total = actual.get('total_requests', -1)
    expected_total = 0  # All lines should be rejected

    if actual_total == 0:
        points = max_points
    elif actual_total >= 14:
        points = 0
    else:
        points = max(0, max_points - actual_total)

    results = [FieldResult(
        field_name='total_requests',
        expected=expected_total,
        actual=actual_total,
        is_correct=(actual_total == 0),
        points=points
    )]

    return points, results


def grade_submission(
    submission_dir: Path,
    hidden_data_dir: Path,
    expected_results: Dict
) -> GradingResult:
    """Grade a complete submission."""

    student_id = submission_dir.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Find executable
    exe_info = find_executable(submission_dir)
    if exe_info is None:
        return GradingResult(
            student_id=student_id,
            timestamp=timestamp,
            total_score=0,
            max_score=100,
            percentage=0,
            grade="F",
            passed=False,
            datasets=[],
            summary="ERROR: Could not find executable (edge_proto_tool/main.py or binary)"
        )

    language, command = exe_info

    # Grade each dataset
    dataset_results = []
    total_score = 0

    for filename, version, category, max_points in DATASETS:
        input_file = hidden_data_dir / filename

        if not input_file.exists():
            dataset_results.append(DatasetResult(
                name=filename,
                version=version,
                category=category,
                points_earned=0,
                points_possible=max_points,
                percentage=0,
                fields=[],
                success=False,
                error_message=f"Test file not found: {filename}"
            ))
            continue

        expected = expected_results.get(filename, {})

        # Run program
        result, stdout, stderr = run_program(command, input_file, submission_dir)

        if result is None:
            dataset_results.append(DatasetResult(
                name=filename,
                version=version,
                category=category,
                points_earned=0,
                points_possible=max_points,
                percentage=0,
                fields=[],
                success=False,
                error_message=stderr or "Program failed to execute"
            ))
            continue

        # Grade based on category
        if category == 'robustness':
            points, fields = grade_robustness(result, expected, max_points)
        else:
            points, fields = grade_correctness(result, expected, max_points)

        total_score += points

        dataset_results.append(DatasetResult(
            name=filename,
            version=version,
            category=category,
            points_earned=points,
            points_possible=max_points,
            percentage=(points / max_points * 100) if max_points > 0 else 0,
            fields=fields,
            success=True,
            error_message=""
        ))

    # Calculate final results
    percentage = total_score
    grade = calculate_grade(percentage)
    passed = total_score >= 60

    return GradingResult(
        student_id=student_id,
        timestamp=timestamp,
        total_score=total_score,
        max_score=100,
        percentage=percentage,
        grade=grade,
        passed=passed,
        datasets=dataset_results,
        summary=f"Score: {total_score:.1f}/100, Grade: {grade}, {'PASSED' if passed else 'FAILED'}"
    )


# =============================================================================
# Output Formatting
# =============================================================================

def print_result(result: GradingResult):
    """Print formatted grading result to console."""

    c = Colors

    print(f"\n{c.BOLD}{'='*60}{c.RESET}")
    print(f"{c.BOLD}GRADING RESULT{c.RESET}")
    print(f"{'='*60}")
    print(f"Student: {result.student_id}")
    print(f"Time:    {result.timestamp}")
    print()

    # Per-dataset results
    for ds in result.datasets:
        pct_bar = "█" * int(ds.percentage / 10) + "░" * (10 - int(ds.percentage / 10))
        status_color = c.GREEN if ds.percentage == 100 else (c.YELLOW if ds.percentage >= 50 else c.RED)

        print(f"{c.BOLD}{ds.name}{c.RESET} ({ds.version}, {ds.category})")

        if not ds.success:
            print(f"  {c.RED}✗ FAILED: {ds.error_message}{c.RESET}")
            print(f"  Points: 0 / {ds.points_possible:.0f}")
        else:
            print(f"  [{pct_bar}] {status_color}{ds.percentage:.0f}%{c.RESET}")
            for f in ds.fields:
                icon = f"{c.GREEN}✓{c.RESET}" if f.is_correct else f"{c.RED}✗{c.RESET}"
                print(f"  {icon} {f.field_name}: expected={f.expected}, actual={f.actual}")
            print(f"  Points: {ds.points_earned:.1f} / {ds.points_possible:.0f}")
        print()

    # Final score
    print(f"{'='*60}")
    status_color = c.GREEN if result.passed else c.RED
    status_text = "PASSED" if result.passed else "FAILED"

    print(f"{c.BOLD}FINAL SCORE: {result.total_score:.1f} / {result.max_score:.0f}{c.RESET}")
    print(f"{c.BOLD}GRADE: {result.grade}{c.RESET}")
    print(f"{c.BOLD}STATUS: {status_color}{status_text}{c.RESET}")
    print(f"{'='*60}\n")


def save_json_result(result: GradingResult, output_file: Path):
    """Save result as JSON file."""

    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_dict(i) for i in obj]
        return obj

    with open(output_file, 'w') as f:
        json.dump(to_dict(result), f, indent=2)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Edge-Proto Challenge Grader')
    parser.add_argument('--submission', required=True, help='Path to student submission directory')
    parser.add_argument('--hidden-data', required=True, help='Path to hidden test data directory')
    parser.add_argument('--expected', required=True, help='Path to expected_results.json')
    parser.add_argument('--output', help='Path to save JSON result (optional)')

    args = parser.parse_args()

    submission_dir = Path(args.submission).resolve()
    hidden_data_dir = Path(args.hidden_data).resolve()
    expected_file = Path(args.expected).resolve()

    # Validate paths
    if not submission_dir.exists():
        print(f"Error: Submission directory not found: {submission_dir}")
        sys.exit(1)

    if not hidden_data_dir.exists():
        print(f"Error: Hidden data directory not found: {hidden_data_dir}")
        sys.exit(1)

    if not expected_file.exists():
        print(f"Error: Expected results file not found: {expected_file}")
        sys.exit(1)

    # Load expected results
    with open(expected_file) as f:
        expected_results = json.load(f)

    # Grade
    result = grade_submission(submission_dir, hidden_data_dir, expected_results)

    # Output
    print_result(result)

    if args.output:
        output_file = Path(args.output)
        save_json_result(result, output_file)
        print(f"JSON result saved to: {output_file}")

    # Exit code: 0 if passed, 1 if failed
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
