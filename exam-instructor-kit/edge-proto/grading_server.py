#!/usr/bin/env python3
"""
Edge-Proto Challenge - Online Grading Server

A simple HTTP server that accepts student submissions and returns grades.

Features:
- API key authentication
- SQLite persistence for all submissions
- Upload ZIP file of submission
- Rate limiting per IP
- Submission size limits

Usage:
    # Generate a new API key
    python grading_server.py --generate-key

    # Start server
    python grading_server.py --port 8123

API Endpoints:
    POST /submit              - Submit ZIP file for grading (requires X-API-Key header)
    GET  /health              - Health check (public)
    GET  /status              - Server stats (public)
    GET  /results             - View all results (requires X-API-Key header)
    GET  /results/<student>   - View student results (requires X-API-Key header)
"""

import argparse
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from collections import defaultdict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse
import threading

# =============================================================================
# Configuration
# =============================================================================

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10  # max submissions per window per IP
GRADING_TIMEOUT = 60  # seconds

# Paths (relative to script directory)
SCRIPT_DIR = Path(__file__).parent.resolve()
HIDDEN_DATA_DIR = SCRIPT_DIR / "hidden_data"
EXPECTED_FILE = SCRIPT_DIR / "expected_results.json"
GRADER_SCRIPT = SCRIPT_DIR / "grader.py"
DATABASE_FILE = SCRIPT_DIR / "grading_results.db"
API_KEY_FILE = SCRIPT_DIR / ".api_key"

# =============================================================================
# API Key Management
# =============================================================================

def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)


def load_api_key() -> Optional[str]:
    """Load API key from file."""
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    return None


def save_api_key(key: str):
    """Save API key to file."""
    API_KEY_FILE.write_text(key)
    os.chmod(API_KEY_FILE, 0o600)  # Only owner can read


def verify_api_key(provided_key: str) -> bool:
    """Verify provided API key."""
    stored_key = load_api_key()
    if stored_key is None:
        return False
    return secrets.compare_digest(provided_key, stored_key)


# =============================================================================
# Database
# =============================================================================

def init_database():
    """Initialize SQLite database."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            total_score REAL,
            grade TEXT,
            passed INTEGER,
            dataset_a REAL,
            dataset_b REAL,
            dataset_c REAL,
            dataset_d REAL,
            result_json TEXT,
            error_message TEXT
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_student_id ON submissions(student_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON submissions(timestamp)
    ''')

    conn.commit()
    conn.close()


def save_submission(student_id: str, ip_address: str, result: dict):
    """Save submission result to database."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()

    if result.get("success"):
        r = result.get("result", {})
        datasets = {ds["name"]: ds["points_earned"] for ds in r.get("datasets", [])}

        cursor.execute('''
            INSERT INTO submissions
            (student_id, timestamp, ip_address, total_score, grade, passed,
             dataset_a, dataset_b, dataset_c, dataset_d, result_json, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            timestamp,
            ip_address,
            r.get("total_score", 0),
            r.get("grade", "F"),
            1 if r.get("passed") else 0,
            datasets.get("edge_proto_v1_A.log", 0),
            datasets.get("edge_proto_v1_B.log", 0),
            datasets.get("edge_proto_v1_1_C.log", 0),
            datasets.get("edge_proto_v1_1_D.log", 0),
            json.dumps(r),
            None
        ))
    else:
        cursor.execute('''
            INSERT INTO submissions
            (student_id, timestamp, ip_address, total_score, grade, passed,
             dataset_a, dataset_b, dataset_c, dataset_d, result_json, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            timestamp,
            ip_address,
            0, "F", 0, 0, 0, 0, 0,
            None,
            result.get("error", "Unknown error")
        ))

    conn.commit()
    conn.close()


def get_all_results() -> list:
    """Get all submission results."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, student_id, timestamp, ip_address, total_score, grade, passed,
               dataset_a, dataset_b, dataset_c, dataset_d, error_message
        FROM submissions
        ORDER BY timestamp DESC
    ''')

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_student_results(student_id: str) -> list:
    """Get results for a specific student."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, student_id, timestamp, ip_address, total_score, grade, passed,
               dataset_a, dataset_b, dataset_c, dataset_d, result_json, error_message
        FROM submissions
        WHERE student_id = ?
        ORDER BY timestamp DESC
    ''', (student_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_stats() -> dict:
    """Get submission statistics."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM submissions')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM submissions WHERE passed = 1')
    passed = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT student_id) FROM submissions')
    unique_students = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(total_score) FROM submissions WHERE total_score > 0')
    avg_score = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_submissions": total,
        "passed": passed,
        "failed": total - passed,
        "unique_students": unique_students,
        "average_score": round(avg_score, 1)
    }


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    def __init__(self, window: int, max_requests: int):
        self.window = window
        self.max_requests = max_requests
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        with self.lock:
            self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
            if len(self.requests[ip]) >= self.max_requests:
                return False
            self.requests[ip].append(now)
            return True

    def remaining(self, ip: str) -> int:
        now = time.time()
        with self.lock:
            self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
            return max(0, self.max_requests - len(self.requests[ip]))


rate_limiter = RateLimiter(RATE_LIMIT_WINDOW, RATE_LIMIT_MAX)

# =============================================================================
# Grading Logic
# =============================================================================

def extract_and_grade(zip_data: bytes, student_id: str) -> dict:
    """Extract ZIP and run grading."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        submission_dir = temp_path / student_id
        submission_dir.mkdir()

        zip_path = temp_path / "submission.zip"
        with open(zip_path, 'wb') as f:
            f.write(zip_data)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for name in zf.namelist():
                    if name.startswith('/') or '..' in name:
                        return {"success": False, "error": "Invalid ZIP: path traversal detected"}
                zf.extractall(submission_dir)
        except zipfile.BadZipFile:
            return {"success": False, "error": "Invalid ZIP file"}

        submission_root = find_submission_root(submission_dir)
        if submission_root is None:
            return {"success": False, "error": "Could not find edge_proto_tool/main.py in submission"}

        result_file = temp_path / "result.json"

        try:
            result = subprocess.run(
                [
                    "python3", str(GRADER_SCRIPT),
                    "--submission", str(submission_root),
                    "--hidden-data", str(HIDDEN_DATA_DIR),
                    "--expected", str(EXPECTED_FILE),
                    "--output", str(result_file)
                ],
                capture_output=True,
                text=True,
                timeout=GRADING_TIMEOUT
            )

            if result_file.exists():
                with open(result_file) as f:
                    return {"success": True, "result": json.load(f)}
            else:
                return {"success": False, "error": f"Grading failed: {result.stderr[:500]}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {GRADING_TIMEOUT}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def find_submission_root(base_dir: Path) -> Optional[Path]:
    """Find the actual submission root directory."""
    if is_valid_submission(base_dir):
        return base_dir

    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            if is_valid_submission(subdir):
                return subdir
            for subsubdir in subdir.iterdir():
                if subsubdir.is_dir() and is_valid_submission(subsubdir):
                    return subsubdir
    return None


def is_valid_submission(path: Path) -> bool:
    """Check if path contains a valid submission."""
    if (path / "edge_proto_tool" / "main.py").exists():
        return True
    if (path / "main.py").exists():
        return True
    if (path / "edge_proto_tool").exists() and (path / "edge_proto_tool").is_file():
        return True
    return False


# =============================================================================
# HTTP Handler
# =============================================================================

class GradingHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.client_address[0]} - {format % args}")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def check_auth(self) -> bool:
        """Check if request has valid API key."""
        api_key = self.headers.get('X-API-Key', '')
        return verify_api_key(api_key)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Student-ID, X-API-Key')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/health':
            self.send_json({"status": "ok", "timestamp": datetime.now().isoformat()})

        elif parsed.path == '/status':
            self.send_json({
                "status": "ok",
                "stats": get_stats(),
                "config": {
                    "max_upload_size_mb": MAX_UPLOAD_SIZE / 1024 / 1024,
                    "rate_limit_per_minute": RATE_LIMIT_MAX,
                }
            })

        elif parsed.path == '/results':
            if not self.check_auth():
                self.send_json({"error": "Unauthorized. Provide X-API-Key header."}, 401)
                return
            self.send_json({"results": get_all_results()})

        elif parsed.path.startswith('/results/'):
            if not self.check_auth():
                self.send_json({"error": "Unauthorized. Provide X-API-Key header."}, 401)
                return
            student_id = parsed.path.split('/results/')[1]
            self.send_json({"student_id": student_id, "results": get_student_results(student_id)})

        elif parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head>
    <title>Edge-Proto Grading Server</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-top: 0; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input[type="text"], input[type="password"] { padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }
        input[type="file"] { padding: 10px; }
        button { padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #1d4ed8; }
        #result { margin-top: 20px; padding: 20px; background: #1e293b; color: #e2e8f0; border-radius: 4px; white-space: pre-wrap; font-family: monospace; font-size: 13px; display: none; }
        .info { background: #dbeafe; padding: 15px; border-radius: 4px; margin-bottom: 20px; color: #1e40af; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Edge-Proto Grading Server</h1>
        <div class="info">
            Upload your submission ZIP file to receive instant grading results.
        </div>
        <form id="gradeForm">
            <div class="form-group">
                <label>API Key:</label>
                <input type="password" id="apiKey" required placeholder="Enter your API key">
            </div>
            <div class="form-group">
                <label>Student ID:</label>
                <input type="text" id="studentId" required placeholder="e.g., student_001">
            </div>
            <div class="form-group">
                <label>Submission (ZIP):</label>
                <input type="file" id="submission" accept=".zip" required>
            </div>
            <button type="submit">Submit for Grading</button>
        </form>
        <div id="result"></div>
    </div>
    <script>
        document.getElementById('gradeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.textContent = 'Grading in progress...';
            const formData = new FormData();
            formData.append('submission', document.getElementById('submission').files[0]);
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'X-Student-ID': document.getElementById('studentId').value,
                        'X-API-Key': document.getElementById('apiKey').value
                    },
                    body: formData
                });
                const data = await response.json();
                resultDiv.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.textContent = 'Error: ' + error.message;
            }
        });
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        client_ip = self.client_address[0]

        if parsed.path == '/submit':
            # Check API key
            if not self.check_auth():
                self.send_json({"error": "Unauthorized. Provide X-API-Key header."}, 401)
                return

            # Rate limiting
            if not rate_limiter.is_allowed(client_ip):
                self.send_json({"error": f"Rate limit exceeded. Try again later."}, 429)
                return

            # Get student ID
            student_id = self.headers.get('X-Student-ID', 'anonymous')
            student_id = ''.join(c for c in student_id if c.isalnum() or c in '_-')[:50]

            # Check content length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > MAX_UPLOAD_SIZE:
                self.send_json({"error": f"File too large. Max {MAX_UPLOAD_SIZE // 1024 // 1024} MB"}, 413)
                return

            # Read body
            body = self.rfile.read(content_length)

            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            zip_data = None

            if 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[1] if 'boundary=' in content_type else None
                if boundary:
                    boundary_bytes = f'--{boundary}'.encode()
                    parts = body.split(boundary_bytes)
                    for part in parts:
                        if b'filename=' in part and b'.zip' in part.lower():
                            data_start = part.find(b'\r\n\r\n')
                            if data_start != -1:
                                zip_data = part[data_start + 4:].rstrip(b'\r\n--')
                                break
            else:
                zip_data = body

            if zip_data is None:
                self.send_json({"error": "No ZIP file found"}, 400)
                return

            # Grade
            self.log_message(f"Grading: {student_id} ({len(zip_data)} bytes)")
            result = extract_and_grade(zip_data, student_id)

            # Save to database
            save_submission(student_id, client_ip, result)

            # Response
            result["student_id"] = student_id
            result["timestamp"] = datetime.now().isoformat()
            self.send_json(result, 200 if result.get("success") else 400)

        else:
            self.send_json({"error": "Not found"}, 404)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Edge-Proto Grading Server')
    parser.add_argument('--port', type=int, default=8123, help='Port to listen on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--generate-key', action='store_true', help='Generate new API key and exit')
    args = parser.parse_args()

    # Generate API key mode
    if args.generate_key:
        key = generate_api_key()
        save_api_key(key)
        print(f"New API key generated and saved to {API_KEY_FILE}")
        print(f"\nYour API key: {key}\n")
        print("Keep this key safe! Share it only with authorized users.")
        return

    # Check API key exists
    if load_api_key() is None:
        print("No API key found. Generating one...")
        key = generate_api_key()
        save_api_key(key)
        print(f"\nYour API key: {key}\n")
        print("Save this key! You'll need it to submit.\n")

    # Verify required files
    for path, name in [(HIDDEN_DATA_DIR, "Hidden data"), (EXPECTED_FILE, "Expected results"), (GRADER_SCRIPT, "Grader")]:
        if not path.exists():
            print(f"Error: {name} not found: {path}")
            return

    # Initialize database
    init_database()

    # Start server
    server = HTTPServer((args.host, args.port), GradingHandler)

    print("=" * 60)
    print("Edge-Proto Grading Server")
    print("=" * 60)
    print(f"URL:        http://{args.host}:{args.port}")
    print(f"Database:   {DATABASE_FILE}")
    print(f"API Key:    {API_KEY_FILE}")
    print("")
    print("Endpoints:")
    print(f"  GET  /           - Web UI")
    print(f"  GET  /health     - Health check")
    print(f"  GET  /status     - Stats")
    print(f"  GET  /results    - All results (auth required)")
    print(f"  POST /submit     - Submit (auth required)")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
