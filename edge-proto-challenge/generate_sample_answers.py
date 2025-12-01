#!/usr/bin/env python3
"""
Generate ground truth answers for sample datasets.
This script calculates the correct statistics for each sample log file.
"""

import json
import os
from pathlib import Path
from collections import Counter

def parse_log_file(filepath):
    """Parse a log file and calculate statistics."""
    total_requests = 0
    error_count = 0
    rtt_sum = 0
    congestion_counter = Counter()
    bad_lines = []

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            fields = line.split(',')

            # Check field count (v1.0 has 10 fields, v1.1 has 11)
            if len(fields) < 10:
                bad_lines.append((line_num, f"insufficient fields: {len(fields)}"))
                continue

            try:
                # Parse required fields
                timestamp = fields[0]  # ISO8601
                stream_id = int(fields[1])
                method = fields[2]
                path = fields[3]
                status = int(fields[4])
                bytes_sent = int(fields[5])
                bytes_recv = int(fields[6])
                rtt_ms = int(fields[7])
                congestion = fields[8]
                quic_version = fields[9]

                # Validate fields
                if not timestamp.endswith('Z'):
                    bad_lines.append((line_num, f"invalid timestamp: {timestamp}"))
                    continue

                if method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
                    bad_lines.append((line_num, f"invalid method: {method}"))
                    continue

                if status < 100 or status > 599:
                    bad_lines.append((line_num, f"invalid status: {status}"))
                    continue

                if congestion not in ('bbr', 'cubic'):
                    bad_lines.append((line_num, f"invalid congestion: {congestion}"))
                    continue

                if not quic_version.startswith('q'):
                    bad_lines.append((line_num, f"invalid quic_version: {quic_version}"))
                    continue

                # Valid line - count it
                total_requests += 1
                rtt_sum += rtt_ms
                congestion_counter[congestion] += 1

                # Count errors (4xx and 5xx)
                if 400 <= status <= 599:
                    error_count += 1

            except (ValueError, IndexError) as e:
                bad_lines.append((line_num, str(e)))
                continue

    # Calculate statistics
    if total_requests > 0:
        error_rate = round(error_count / total_requests, 2)
        avg_rtt_ms = round(rtt_sum / total_requests, 1)
        top_congestion = congestion_counter.most_common(1)[0][0]
    else:
        error_rate = 0.0
        avg_rtt_ms = 0.0
        top_congestion = "unknown"

    return {
        "total_requests": total_requests,
        "error_rate": error_rate,
        "avg_rtt_ms": avg_rtt_ms,
        "top_congestion": top_congestion
    }, bad_lines


def main():
    sample_dir = Path(__file__).parent / "data" / "sample"

    results = {}

    for log_file in sorted(sample_dir.glob("*.log")):
        print(f"\n{'='*60}")
        print(f"Processing: {log_file.name}")
        print('='*60)

        stats, bad_lines = parse_log_file(log_file)
        results[log_file.name] = stats

        print(f"Results:")
        print(json.dumps(stats, indent=2))

        if bad_lines:
            print(f"\nBad lines ({len(bad_lines)}):")
            for line_num, reason in bad_lines[:5]:
                print(f"  Line {line_num}: {reason}")
            if len(bad_lines) > 5:
                print(f"  ... and {len(bad_lines) - 5} more")

    # Save results
    output_file = sample_dir / "expected_answers.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nSaved to: {output_file}")
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, stats in results.items():
        print(f"\n{name}:")
        print(f"  total_requests: {stats['total_requests']}")
        print(f"  error_rate: {stats['error_rate']}")
        print(f"  avg_rtt_ms: {stats['avg_rtt_ms']}")
        print(f"  top_congestion: {stats['top_congestion']}")


if __name__ == '__main__':
    main()
