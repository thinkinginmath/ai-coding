#!/usr/bin/env python3
"""
Detailed grading report generator for edge-proto-challenge.

Generates a comprehensive report with:
- Overall score and grade
- Per-dataset breakdown
- Per-field accuracy
- Robustness analysis
- Recommendations

Usage:
    python grading_report.py <submission_dir> [--output report.json]
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class FieldResult:
    """Result for a single field comparison."""
    field_name: str
    expected: Any
    actual: Any
    is_correct: bool
    points_earned: float
    points_possible: float


@dataclass
class DatasetResult:
    """Result for a single dataset."""
    dataset_name: str
    version: str  # "v1.0" or "v1.1"
    category: str  # "correctness" or "robustness"
    points_earned: float
    points_possible: float
    percentage: float
    field_results: List[FieldResult]
    execution_success: bool
    stderr_output: str
    has_warnings: bool


@dataclass
class GradingReport:
    """Complete grading report."""
    candidate_id: str
    timestamp: str

    # Scores
    total_score: float
    max_score: float
    percentage: float
    grade: str
    passed: bool

    # Breakdown
    correctness_score: float
    correctness_max: float
    robustness_score: float
    robustness_max: float

    # Details
    dataset_results: List[DatasetResult]

    # Summary
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


def calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


def get_grade_description(grade: str) -> str:
    """Get description for grade."""
    descriptions = {
        "A": "Excellent - Demonstrates mastery of log parsing and robust error handling",
        "B": "Good - Solid implementation with minor issues",
        "C": "Satisfactory - Meets basic requirements but has notable gaps",
        "D": "Passing - Minimum acceptable, significant improvement needed",
        "F": "Fail - Does not meet minimum requirements"
    }
    return descriptions.get(grade, "Unknown")


def analyze_strengths_weaknesses(dataset_results: List[DatasetResult]) -> tuple:
    """Analyze results to identify strengths and weaknesses."""
    strengths = []
    weaknesses = []
    recommendations = []

    # Check each dataset
    for result in dataset_results:
        if result.percentage == 100:
            if result.category == "correctness":
                strengths.append(f"Perfect score on {result.dataset_name} ({result.version})")
            else:
                strengths.append(f"Excellent robustness - all bad lines correctly handled")
        elif result.percentage >= 75:
            strengths.append(f"Good performance on {result.dataset_name}")
        elif result.percentage < 50:
            weaknesses.append(f"Poor performance on {result.dataset_name} ({result.percentage:.0f}%)")

    # Check field-level issues
    field_issues = {}
    for result in dataset_results:
        for field in result.field_results:
            if not field.is_correct:
                if field.field_name not in field_issues:
                    field_issues[field.field_name] = 0
                field_issues[field.field_name] += 1

    for field, count in field_issues.items():
        if count > 1:
            weaknesses.append(f"Recurring issue with '{field}' field ({count} datasets)")
            if field == "total_requests":
                recommendations.append("Review bad line detection logic - some valid/invalid lines may be miscounted")
            elif field == "error_rate":
                recommendations.append("Check error rate calculation - ensure 4xx/5xx status codes are correctly identified")
            elif field == "avg_rtt_ms":
                recommendations.append("Verify RTT averaging - check for off-by-one errors or incorrect rounding")
            elif field == "top_congestion":
                recommendations.append("Review congestion algorithm counting logic")

    # Check warning output
    has_any_warnings = any(r.has_warnings for r in dataset_results)
    if has_any_warnings:
        strengths.append("Program outputs warnings for invalid lines (good practice)")
    else:
        recommendations.append("Consider adding warning output to stderr for invalid lines")

    return strengths, weaknesses, recommendations


def generate_text_report(report: GradingReport) -> str:
    """Generate human-readable text report."""
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("EDGE-PROTO CHALLENGE - GRADING REPORT")
    lines.append("=" * 70)
    lines.append(f"Candidate: {report.candidate_id}")
    lines.append(f"Date: {report.timestamp}")
    lines.append("")

    # Overall Score
    lines.append("-" * 70)
    lines.append("OVERALL SCORE")
    lines.append("-" * 70)
    lines.append(f"  Total: {report.total_score:.1f} / {report.max_score:.0f} ({report.percentage:.1f}%)")
    lines.append(f"  Grade: {report.grade} - {get_grade_description(report.grade)}")
    lines.append(f"  Status: {'PASSED' if report.passed else 'FAILED'}")
    lines.append("")

    # Score Breakdown
    lines.append("-" * 70)
    lines.append("SCORE BREAKDOWN")
    lines.append("-" * 70)

    correctness_pct = (report.correctness_score / report.correctness_max * 100) if report.correctness_max > 0 else 0
    robustness_pct = (report.robustness_score / report.robustness_max * 100) if report.robustness_max > 0 else 0

    lines.append(f"  Correctness:  {report.correctness_score:5.1f} / {report.correctness_max:5.0f}  ({correctness_pct:5.1f}%)")
    lines.append(f"  Robustness:   {report.robustness_score:5.1f} / {report.robustness_max:5.0f}  ({robustness_pct:5.1f}%)")
    lines.append("")

    # Per-Dataset Results
    lines.append("-" * 70)
    lines.append("DATASET RESULTS")
    lines.append("-" * 70)

    for result in report.dataset_results:
        status = "✓" if result.percentage == 100 else ("◐" if result.percentage >= 50 else "✗")
        bar_filled = int(result.percentage / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        lines.append(f"\n  {result.dataset_name} ({result.version}, {result.category})")
        lines.append(f"    Score: {result.points_earned:.1f} / {result.points_possible:.0f}  [{bar}] {result.percentage:.0f}%")

        if not result.execution_success:
            lines.append(f"    {status} Program failed to execute")
        elif result.field_results:
            for field in result.field_results:
                field_status = "✓" if field.is_correct else "✗"
                lines.append(f"    {field_status} {field.field_name}: expected={field.expected}, actual={field.actual}")

    lines.append("")

    # Strengths
    if report.strengths:
        lines.append("-" * 70)
        lines.append("STRENGTHS")
        lines.append("-" * 70)
        for s in report.strengths:
            lines.append(f"  ✓ {s}")
        lines.append("")

    # Weaknesses
    if report.weaknesses:
        lines.append("-" * 70)
        lines.append("AREAS FOR IMPROVEMENT")
        lines.append("-" * 70)
        for w in report.weaknesses:
            lines.append(f"  • {w}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("-" * 70)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        for r in report.recommendations:
            lines.append(f"  → {r}")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)


def run_candidate_program(
    command_parts: List[str],
    input_file: Path,
    working_dir: Path,
    timeout: int = 30
) -> tuple:
    """Run the candidate's program on an input file."""
    try:
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

        try:
            parsed = json.loads(stdout)
            return parsed, stdout, stderr
        except json.JSONDecodeError as e:
            return None, stdout, f"{stderr}\nJSON parse error: {str(e)}"

    except subprocess.TimeoutExpired:
        return None, "", f"Program timed out after {timeout} seconds"
    except Exception as e:
        return None, "", f"Execution error: {str(e)}"


def find_executable(submission_dir: Path):
    """Detect how to run the candidate's program."""
    python_patterns = [
        submission_dir / 'edge_proto_tool' / 'main.py',
        submission_dir / 'src' / 'edge_proto_tool' / 'main.py',
        submission_dir / 'main.py',
    ]

    for py_file in python_patterns:
        if py_file.exists():
            if 'edge_proto_tool' in str(py_file):
                return ('python', ['python3', '-m', 'edge_proto_tool.main'])
            else:
                return ('python', ['python3', str(py_file)])

    go_patterns = [
        submission_dir / 'edge_proto_tool',
        submission_dir / 'main',
        submission_dir / 'bin' / 'edge_proto_tool',
    ]

    for go_binary in go_patterns:
        if go_binary.exists() and go_binary.is_file():
            return ('go', [str(go_binary)])

    return None


def grade_submission(submission_dir: Path, expected_results: Dict, hidden_data_dir: Path) -> GradingReport:
    """Grade a submission and generate a detailed report."""

    candidate_id = submission_dir.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    executable_info = find_executable(submission_dir)
    if executable_info is None:
        # Return a failed report
        return GradingReport(
            candidate_id=candidate_id,
            timestamp=timestamp,
            total_score=0,
            max_score=100,
            percentage=0,
            grade="F",
            passed=False,
            correctness_score=0,
            correctness_max=86,
            robustness_score=0,
            robustness_max=14,
            dataset_results=[],
            strengths=[],
            weaknesses=["Could not find executable program in submission"],
            recommendations=["Ensure edge_proto_tool/main.py exists for Python or compiled binary for Go"]
        )

    language, command_parts = executable_info

    # Dataset configuration
    datasets = [
        ('edge_proto_v1_A.log', 'v1.0', 'correctness', 20),
        ('edge_proto_v1_B.log', 'v1.0', 'correctness', 30),
        ('edge_proto_v1_1_C.log', 'v1.1', 'correctness', 36),
        ('edge_proto_v1_1_D.log', 'v1.1', 'robustness', 14),
    ]

    tolerance = {
        'error_rate': 0.01,
        'avg_rtt_ms': 0.5,
    }

    dataset_results = []
    total_score = 0
    correctness_score = 0
    robustness_score = 0

    for dataset_name, version, category, max_points in datasets:
        input_file = hidden_data_dir / dataset_name
        expected = expected_results.get(dataset_name, {})

        result, stdout, stderr = run_candidate_program(
            command_parts, input_file, submission_dir
        )

        has_warnings = stderr and 'warning' in stderr.lower()

        if result is None:
            # Execution failed
            dataset_results.append(DatasetResult(
                dataset_name=dataset_name,
                version=version,
                category=category,
                points_earned=0,
                points_possible=max_points,
                percentage=0,
                field_results=[],
                execution_success=False,
                stderr_output=stderr[:500] if stderr else "",
                has_warnings=False
            ))
            continue

        if category == 'robustness':
            # Special handling for Dataset D
            actual_total = result.get('total_requests', 0)
            if actual_total == 0:
                points = max_points
            elif actual_total >= 14:
                points = 0
            else:
                points = max_points - actual_total

            field_results = [FieldResult(
                field_name='total_requests',
                expected=0,
                actual=actual_total,
                is_correct=(actual_total == 0),
                points_earned=points,
                points_possible=max_points
            )]

            robustness_score += points
            total_score += points

            dataset_results.append(DatasetResult(
                dataset_name=dataset_name,
                version=version,
                category=category,
                points_earned=points,
                points_possible=max_points,
                percentage=(points / max_points * 100) if max_points > 0 else 0,
                field_results=field_results,
                execution_success=True,
                stderr_output=stderr[:500] if stderr else "",
                has_warnings=has_warnings
            ))
        else:
            # Normal correctness grading
            field_results = []
            correct_count = 0

            fields = ['total_requests', 'error_rate', 'avg_rtt_ms', 'top_congestion']
            for field in fields:
                expected_val = expected.get(field)
                actual_val = result.get(field)

                if field in tolerance:
                    is_correct = abs(float(actual_val or 0) - float(expected_val or 0)) <= tolerance[field]
                else:
                    is_correct = actual_val == expected_val

                if is_correct:
                    correct_count += 1

                field_points = max_points / 4
                field_results.append(FieldResult(
                    field_name=field,
                    expected=expected_val,
                    actual=actual_val,
                    is_correct=is_correct,
                    points_earned=field_points if is_correct else 0,
                    points_possible=field_points
                ))

            points = (correct_count / 4) * max_points
            correctness_score += points
            total_score += points

            dataset_results.append(DatasetResult(
                dataset_name=dataset_name,
                version=version,
                category=category,
                points_earned=points,
                points_possible=max_points,
                percentage=(points / max_points * 100) if max_points > 0 else 0,
                field_results=field_results,
                execution_success=True,
                stderr_output=stderr[:500] if stderr else "",
                has_warnings=has_warnings
            ))

    # Calculate overall
    percentage = (total_score / 100) * 100
    grade = calculate_grade(percentage)
    passed = total_score >= 60

    # Analyze strengths and weaknesses
    strengths, weaknesses, recommendations = analyze_strengths_weaknesses(dataset_results)

    return GradingReport(
        candidate_id=candidate_id,
        timestamp=timestamp,
        total_score=total_score,
        max_score=100,
        percentage=percentage,
        grade=grade,
        passed=passed,
        correctness_score=correctness_score,
        correctness_max=86,
        robustness_score=robustness_score,
        robustness_max=14,
        dataset_results=dataset_results,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python grading_report.py <submission_dir> [--output report.json]")
        sys.exit(1)

    submission_dir = Path(sys.argv[1]).resolve()
    output_file = None

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = Path(sys.argv[idx + 1])

    if not submission_dir.exists():
        print(f"Error: Submission directory not found: {submission_dir}")
        sys.exit(1)

    # Load expected results
    script_dir = Path(__file__).parent
    expected_file = script_dir / 'expected_results.json'

    if not expected_file.exists():
        print("Error: expected_results.json not found")
        sys.exit(1)

    with open(expected_file, 'r') as f:
        expected_results = json.load(f)

    # Find hidden data
    repo_root = script_dir.parent.parent
    hidden_data_dir = repo_root / 'edge-proto-challenge' / 'data' / 'hidden'

    if not hidden_data_dir.exists():
        print(f"Error: Hidden data directory not found: {hidden_data_dir}")
        sys.exit(1)

    # Generate report
    report = grade_submission(submission_dir, expected_results, hidden_data_dir)

    # Output text report
    print(generate_text_report(report))

    # Optionally save JSON
    if output_file:
        # Convert dataclasses to dict
        def to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: to_dict(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [to_dict(item) for item in obj]
            else:
                return obj

        with open(output_file, 'w') as f:
            json.dump(to_dict(report), f, indent=2)
        print(f"\nJSON report saved to: {output_file}")


if __name__ == '__main__':
    main()
