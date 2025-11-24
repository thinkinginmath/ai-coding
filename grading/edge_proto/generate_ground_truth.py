#!/usr/bin/env python3
"""
Generate ground truth results for edge-proto-challenge hidden datasets.

This script parses the hidden test data and generates expected JSON outputs
that will be used to grade candidate submissions.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter


def parse_log_line(line: str, line_num: int) -> Tuple[Dict, str]:
    """
    Parse a single log line and return parsed data or None if invalid.

    Returns:
        (parsed_dict, error_msg) - error_msg is empty string if valid
    """
    line = line.strip()

    # Skip empty lines
    if not line:
        return None, "empty line"

    # Skip comment lines
    if line.startswith('#'):
        return None, "comment line"

    parts = line.split(',')

    # v1.0 has 10 fields, v1.1 has 11 fields
    if len(parts) < 10:
        return None, f"insufficient fields: expected 10-11, got {len(parts)}"

    try:
        data = {
            'timestamp': parts[0],
            'stream_id': int(parts[1]),
            'method': parts[2],
            'path': parts[3],
            'status': int(parts[4]),
            'bytes_sent': int(parts[5]),
            'bytes_recv': int(parts[6]),
            'rtt_ms': int(parts[7]),
            'congestion': parts[8],
            'quic_version': parts[9],
        }

        # v1.1 extended field
        if len(parts) >= 11:
            data['edge_cache_status'] = parts[10]

        return data, ""

    except (ValueError, IndexError) as e:
        return None, f"parsing error: {str(e)}"


def calculate_stats(log_file: Path) -> Dict:
    """
    Calculate statistics from a log file.

    Returns:
        Dictionary with total_requests, error_rate, avg_rtt_ms, top_congestion
    """
    valid_requests = []
    congestion_counts = Counter()

    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            data, error = parse_log_line(line, line_num)

            if data is None:
                # Skip invalid lines (consistent with challenge requirements)
                if error and not error.startswith("empty") and not error.startswith("comment"):
                    print(f"  Warning line {line_num}: {error}", file=sys.stderr)
                continue

            valid_requests.append(data)
            congestion_counts[data['congestion']] += 1

    if not valid_requests:
        return {
            'total_requests': 0,
            'error_rate': 0.0,
            'avg_rtt_ms': 0.0,
            'top_congestion': ''
        }

    # Calculate metrics
    total_requests = len(valid_requests)
    error_count = sum(1 for r in valid_requests if r['status'] >= 400)
    error_rate = error_count / total_requests if total_requests > 0 else 0.0

    total_rtt = sum(r['rtt_ms'] for r in valid_requests)
    avg_rtt_ms = total_rtt / total_requests if total_requests > 0 else 0.0

    top_congestion = congestion_counts.most_common(1)[0][0] if congestion_counts else ''

    return {
        'total_requests': total_requests,
        'error_rate': round(error_rate, 2),
        'avg_rtt_ms': round(avg_rtt_ms, 1),
        'top_congestion': top_congestion
    }


def main():
    """Generate ground truth for all hidden datasets."""

    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    hidden_data_dir = repo_root / 'edge-proto-challenge' / 'data' / 'hidden'
    output_file = script_dir / 'expected_results.json'

    if not hidden_data_dir.exists():
        print(f"Error: Hidden data directory not found: {hidden_data_dir}")
        sys.exit(1)

    print("Generating ground truth results...")
    print(f"Input directory: {hidden_data_dir}")
    print()

    results = {}

    # Process each dataset
    datasets = [
        'edge_proto_v1_A.log',
        'edge_proto_v1_B.log',
        'edge_proto_v1_1_C.log'
    ]

    for dataset_name in datasets:
        log_file = hidden_data_dir / dataset_name

        if not log_file.exists():
            print(f"Warning: {dataset_name} not found, skipping")
            continue

        print(f"Processing {dataset_name}...")
        stats = calculate_stats(log_file)
        results[dataset_name] = stats

        print(f"  total_requests: {stats['total_requests']}")
        print(f"  error_rate: {stats['error_rate']}")
        print(f"  avg_rtt_ms: {stats['avg_rtt_ms']}")
        print(f"  top_congestion: {stats['top_congestion']}")
        print()

    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Ground truth saved to: {output_file}")
    print("\nYou can now use grader.py to test candidate submissions.")


if __name__ == '__main__':
    main()
