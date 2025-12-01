#!/usr/bin/env python3
"""
Unified Grading Server - Edge-Proto & Frontend Dashboard Challenges

A HTTP server that accepts student submissions and returns grades for both challenges.

Features:
- API key authentication
- SQLite persistence for all submissions
- Upload ZIP file of submission
- Rate limiting per IP
- Support for both edge-proto (backend) and frontend challenges
- SANDBOXING: Code scanning, resource limits, and optional firejail/bubblewrap

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

Submit Headers:
    X-API-Key: <api_key>        - Required authentication
    X-Student-ID: <student_id>  - Student identifier
    X-Challenge: <challenge>    - "edge-proto" (default) or "frontend"
"""

import argparse
import json
import os
import re
import resource
import secrets
import shutil
import signal
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from collections import defaultdict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import threading

# =============================================================================
# Configuration
# =============================================================================

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB (frontend projects can be larger)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10  # max submissions per window per IP
GRADING_TIMEOUT = 120  # seconds (frontend tests take longer)

# Paths (relative to script directory)
SCRIPT_DIR = Path(__file__).parent.resolve()
DATABASE_FILE = SCRIPT_DIR / "grading_results.db"
API_KEY_FILE = SCRIPT_DIR / ".api_key"

# Challenge-specific paths
EDGE_PROTO_DIR = SCRIPT_DIR / "edge-proto"
FRONTEND_DIR = SCRIPT_DIR / "frontend-dashboard"

# Sandbox settings
SANDBOX_ENABLED = True
SANDBOX_MAX_CPU_TIME = 60  # seconds
SANDBOX_MAX_MEMORY = 512 * 1024 * 1024  # 512 MB
SANDBOX_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
SANDBOX_MAX_PROCESSES = 50
SANDBOX_MAX_OPEN_FILES = 256

# =============================================================================
# Sandbox - Security Module
# =============================================================================

# Dangerous patterns to detect in submitted code
DANGEROUS_PATTERNS = [
    # Destructive file operations
    (r'\brm\s+(-[rRfF]+\s+)*[/~]', "Dangerous rm command detected"),
    (r'\brm\s+-[rRfF]*\s+\*', "Dangerous rm with wildcard detected"),
    (r'shutil\.rmtree\s*\(\s*[\'"][/~]', "Dangerous rmtree on system path"),
    (r'os\.remove\s*\(\s*[\'"][/~]', "Dangerous os.remove on system path"),
    (r'os\.unlink\s*\(\s*[\'"][/~]', "Dangerous os.unlink on system path"),

    # System modification
    (r'\bdd\s+.*of=/dev/', "Dangerous dd command detected"),
    (r'\bmkfs\.', "Filesystem format command detected"),
    (r'\bfdisk\b', "Disk partition command detected"),
    (r'>\s*/dev/[sh]d[a-z]', "Write to disk device detected"),
    (r'>\s*/etc/', "Write to /etc detected"),
    (r'>\s*/usr/', "Write to /usr detected"),
    (r'>\s*/bin/', "Write to /bin detected"),
    (r'>\s*/sbin/', "Write to /sbin detected"),

    # Fork bombs and resource exhaustion
    (r':\(\)\{\s*:\|:&\s*\};:', "Fork bomb detected"),
    (r'while\s*\(?\s*true\s*\)?\s*;?\s*do.*fork', "Fork loop detected"),
    (r'for\s*\(\s*;\s*;\s*\).*fork', "Infinite fork loop detected"),

    # Network attacks
    (r'\bnetcat\b|\bnc\s+-[el]', "Netcat listener detected"),
    (r'\b(wget|curl).*\|\s*(ba)?sh', "Remote code execution attempt"),
    (r'python.*-c.*socket', "Python socket in one-liner"),
    (r'bash\s+-i\s+>&\s*/dev/tcp/', "Reverse shell attempt"),

    # Privilege escalation
    (r'\bsudo\b', "sudo command detected"),
    (r'\bsu\s+-', "su command detected"),
    (r'\bchmod\s+[0-7]*[sS]', "setuid/setgid chmod detected"),
    (r'\bchown\s+root', "chown to root detected"),

    # Crypto mining / malware indicators
    (r'\bxmrig\b|\bminerd\b|\bcgminer\b', "Crypto miner detected"),
    (r'stratum\+tcp://', "Mining pool connection detected"),

    # Data exfiltration
    (r'curl.*-d.*@/etc/passwd', "Password file exfiltration"),
    (r'cat\s+/etc/(passwd|shadow)', "Reading system passwords"),

    # Python-specific dangerous operations
    (r'exec\s*\(\s*.*input', "Dangerous exec with input"),
    (r'eval\s*\(\s*.*input', "Dangerous eval with input"),
    (r'__import__\s*\(\s*[\'"]os[\'"]\s*\)\.system', "Hidden os.system call"),
    (r'subprocess\..*shell\s*=\s*True.*input', "Shell injection risk"),

    # Node.js specific
    (r'child_process.*exec.*\+', "Command injection in Node.js"),
    (r'require\s*\(\s*[\'"]child_process[\'"]\s*\).*exec\s*\(.*\+', "Dynamic command execution"),
]

# File extensions to scan
SCANNABLE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.sh', '.bash', '.go', '.rs'}


def scan_code_for_dangers(directory: Path) -> Tuple[bool, List[str]]:
    """
    Scan all code files in directory for dangerous patterns.
    Returns (is_safe, list_of_warnings).
    """
    warnings = []

    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue

        # Skip node_modules, .git, etc.
        if any(part.startswith('.') or part == 'node_modules' for part in file_path.parts):
            continue

        # Only scan known code files
        if file_path.suffix.lower() not in SCANNABLE_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(errors='ignore')
            rel_path = file_path.relative_to(directory)

            for pattern, message in DANGEROUS_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    warnings.append(f"{rel_path}: {message}")

        except Exception as e:
            # Skip files we can't read
            pass

    is_safe = len(warnings) == 0
    return is_safe, warnings


def detect_sandbox_tool() -> Optional[str]:
    """Detect available sandboxing tools."""
    # Check for firejail (most feature-rich)
    try:
        result = subprocess.run(['firejail', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'firejail'
    except:
        pass

    # Check for bubblewrap (lightweight)
    try:
        result = subprocess.run(['bwrap', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'bubblewrap'
    except:
        pass

    # Fallback to basic resource limits
    return None


SANDBOX_TOOL = None  # Will be set on startup


def set_resource_limits():
    """Set resource limits for child process (used with preexec_fn)."""
    try:
        # CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (SANDBOX_MAX_CPU_TIME, SANDBOX_MAX_CPU_TIME))

        # Memory limit (address space)
        resource.setrlimit(resource.RLIMIT_AS, (SANDBOX_MAX_MEMORY, SANDBOX_MAX_MEMORY))

        # File size limit
        resource.setrlimit(resource.RLIMIT_FSIZE, (SANDBOX_MAX_FILE_SIZE, SANDBOX_MAX_FILE_SIZE))

        # Number of processes
        resource.setrlimit(resource.RLIMIT_NPROC, (SANDBOX_MAX_PROCESSES, SANDBOX_MAX_PROCESSES))

        # Number of open files
        resource.setrlimit(resource.RLIMIT_NOFILE, (SANDBOX_MAX_OPEN_FILES, SANDBOX_MAX_OPEN_FILES))

        # Core dump size (disable)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    except Exception as e:
        print(f"Warning: Could not set resource limits: {e}")


def get_safe_environment() -> dict:
    """Get a sanitized environment for running untrusted code."""
    # Start with minimal environment
    safe_env = {
        'PATH': '/usr/local/bin:/usr/bin:/bin',
        'HOME': '/tmp',
        'LANG': 'C.UTF-8',
        'LC_ALL': 'C.UTF-8',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONUNBUFFERED': '1',
        'NODE_ENV': 'production',
    }

    # Copy some safe variables from current environment
    for var in ['TERM', 'TZ']:
        if var in os.environ:
            safe_env[var] = os.environ[var]

    return safe_env


def wrap_command_with_sandbox(command: List[str], working_dir: Path) -> List[str]:
    """Wrap a command with sandbox tool if available."""
    global SANDBOX_TOOL

    if not SANDBOX_ENABLED or SANDBOX_TOOL is None:
        return command

    if SANDBOX_TOOL == 'firejail':
        # Firejail with strict options
        return [
            'firejail',
            '--quiet',
            '--private',  # Private home directory
            '--private-tmp',  # Private /tmp
            '--private-dev',  # Limited /dev
            '--net=none',  # No network (for edge-proto)
            '--noroot',  # Drop root privileges
            '--rlimit-cpu=60',  # CPU time limit
            '--rlimit-as=536870912',  # Memory limit
            '--rlimit-fsize=52428800',  # File size limit
            '--rlimit-nproc=50',  # Process limit
            f'--whitelist={working_dir}',
            '--read-only=/usr',
            '--read-only=/lib',
            '--read-only=/lib64',
        ] + command

    elif SANDBOX_TOOL == 'bubblewrap':
        # Bubblewrap with isolation
        return [
            'bwrap',
            '--ro-bind', '/usr', '/usr',
            '--ro-bind', '/lib', '/lib',
            '--ro-bind', '/lib64', '/lib64',
            '--ro-bind', '/bin', '/bin',
            '--ro-bind', '/sbin', '/sbin',
            '--bind', str(working_dir), str(working_dir),
            '--tmpfs', '/tmp',
            '--proc', '/proc',
            '--dev', '/dev',
            '--unshare-net',  # No network
            '--unshare-pid',  # PID namespace
            '--unshare-ipc',  # IPC namespace
            '--die-with-parent',
            '--chdir', str(working_dir),
        ] + command

    return command


def run_sandboxed(
    command: List[str],
    working_dir: Path,
    timeout: int = GRADING_TIMEOUT,
    capture_output: bool = True,
    allow_network: bool = False
) -> subprocess.CompletedProcess:
    """
    Run a command in a sandboxed environment.
    """
    # Wrap with sandbox tool if available
    sandboxed_cmd = wrap_command_with_sandbox(command, working_dir)

    return subprocess.run(
        sandboxed_cmd,
        cwd=working_dir,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
        env=get_safe_environment(),
        preexec_fn=set_resource_limits
    )


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
    os.chmod(API_KEY_FILE, 0o600)


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
            challenge TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            total_score REAL,
            max_score REAL,
            grade TEXT,
            passed INTEGER,
            result_json TEXT,
            error_message TEXT
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_student_id ON submissions(student_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_challenge ON submissions(challenge)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON submissions(timestamp)
    ''')

    conn.commit()
    conn.close()


def save_submission(student_id: str, challenge: str, ip_address: str, result: dict):
    """Save submission result to database."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()

    if result.get("success"):
        r = result.get("result", {})
        cursor.execute('''
            INSERT INTO submissions
            (student_id, challenge, timestamp, ip_address, total_score, max_score,
             grade, passed, result_json, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            challenge,
            timestamp,
            ip_address,
            r.get("total_score", 0),
            r.get("max_score", 100),
            r.get("grade", "F"),
            1 if r.get("passed") else 0,
            json.dumps(r),
            None
        ))
    else:
        cursor.execute('''
            INSERT INTO submissions
            (student_id, challenge, timestamp, ip_address, total_score, max_score,
             grade, passed, result_json, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            challenge,
            timestamp,
            ip_address,
            0, 100, "F", 0, None,
            result.get("error", "Unknown error")
        ))

    conn.commit()
    conn.close()


def get_all_results(challenge: Optional[str] = None) -> list:
    """Get all submission results."""
    conn = sqlite3.connect(str(DATABASE_FILE))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if challenge:
        cursor.execute('''
            SELECT id, student_id, challenge, timestamp, ip_address, total_score,
                   max_score, grade, passed, error_message
            FROM submissions
            WHERE challenge = ?
            ORDER BY timestamp DESC
        ''', (challenge,))
    else:
        cursor.execute('''
            SELECT id, student_id, challenge, timestamp, ip_address, total_score,
                   max_score, grade, passed, error_message
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
        SELECT id, student_id, challenge, timestamp, ip_address, total_score,
               max_score, grade, passed, result_json, error_message
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

    stats = {"challenges": {}}

    for challenge in ["edge-proto", "frontend"]:
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE challenge = ?', (challenge,))
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM submissions WHERE challenge = ? AND passed = 1', (challenge,))
        passed = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT student_id) FROM submissions WHERE challenge = ?', (challenge,))
        unique = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(total_score) FROM submissions WHERE challenge = ? AND total_score > 0', (challenge,))
        avg = cursor.fetchone()[0] or 0

        stats["challenges"][challenge] = {
            "total_submissions": total,
            "passed": passed,
            "failed": total - passed,
            "unique_students": unique,
            "average_score": round(avg, 1)
        }

    cursor.execute('SELECT COUNT(*) FROM submissions')
    stats["total_submissions"] = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT student_id) FROM submissions')
    stats["unique_students"] = cursor.fetchone()[0]

    conn.close()
    return stats


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


rate_limiter = RateLimiter(RATE_LIMIT_WINDOW, RATE_LIMIT_MAX)


# =============================================================================
# Edge-Proto Grading
# =============================================================================

def grade_edge_proto(zip_data: bytes, student_id: str) -> dict:
    """Grade edge-proto challenge submission."""
    grader_script = EDGE_PROTO_DIR / "grader.py"
    hidden_data = EDGE_PROTO_DIR / "hidden_data"
    expected_file = EDGE_PROTO_DIR / "expected_results.json"

    for path, name in [(grader_script, "Grader"), (hidden_data, "Hidden data"), (expected_file, "Expected results")]:
        if not path.exists():
            return {"success": False, "error": f"Server config error: {name} not found"}

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

        # SECURITY: Scan code for dangerous patterns
        if SANDBOX_ENABLED:
            is_safe, warnings = scan_code_for_dangers(submission_dir)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"SECURITY: Dangerous code detected - submission rejected",
                    "security_warnings": warnings[:10]  # Limit to first 10
                }

        # Find submission root
        submission_root = find_edge_proto_root(submission_dir)
        if submission_root is None:
            return {"success": False, "error": "Could not find edge_proto_tool/main.py or binary in submission"}

        result_file = temp_path / "result.json"

        try:
            # Run grader with sandboxing
            # Note: The grader itself runs the student code, so we apply limits there
            result = subprocess.run(
                [
                    "python3", str(grader_script),
                    "--submission", str(submission_root),
                    "--hidden-data", str(hidden_data),
                    "--expected", str(expected_file),
                    "--output", str(result_file)
                ],
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=GRADING_TIMEOUT,
                env=get_safe_environment() if SANDBOX_ENABLED else None,
                preexec_fn=set_resource_limits if SANDBOX_ENABLED else None
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


def find_edge_proto_root(base_dir: Path) -> Optional[Path]:
    """Find the actual submission root directory."""
    if is_valid_edge_proto(base_dir):
        return base_dir

    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            if is_valid_edge_proto(subdir):
                return subdir
            for subsubdir in subdir.iterdir():
                if subsubdir.is_dir() and is_valid_edge_proto(subsubdir):
                    return subsubdir
    return None


def is_valid_edge_proto(path: Path) -> bool:
    """Check if path contains a valid edge-proto submission."""
    if (path / "edge_proto_tool" / "main.py").exists():
        return True
    if (path / "main.py").exists():
        return True
    if (path / "edge_proto_tool").exists() and (path / "edge_proto_tool").is_file():
        return True
    return False


# =============================================================================
# Frontend Grading
# =============================================================================

def grade_frontend(zip_data: bytes, student_id: str) -> dict:
    """Grade frontend dashboard challenge submission."""
    grader_spec = FRONTEND_DIR / "grader.spec.js"
    mock_api = FRONTEND_DIR / "mock-api-server.js"
    playwright_config = FRONTEND_DIR / "playwright.config.js"

    for path, name in [(grader_spec, "Grader spec"), (mock_api, "Mock API")]:
        if not path.exists():
            return {"success": False, "error": f"Server config error: {name} not found"}

    # Check if node/npm is available
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"success": False, "error": "Node.js not installed on grading server"}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        submission_dir = temp_path / "submission"
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

        # SECURITY: Scan code for dangerous patterns
        if SANDBOX_ENABLED:
            is_safe, warnings = scan_code_for_dangers(submission_dir)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"SECURITY: Dangerous code detected - submission rejected",
                    "security_warnings": warnings[:10]
                }

        # Find submission root (contains package.json)
        submission_root = find_frontend_root(submission_dir)
        if submission_root is None:
            return {"success": False, "error": "Could not find package.json in submission"}

        # Set up grading environment
        grading_dir = temp_path / "grading"
        grading_dir.mkdir()

        # Copy grading files
        shutil.copy(grader_spec, grading_dir)
        shutil.copy(mock_api, grading_dir)
        shutil.copy(playwright_config, grading_dir)
        shutil.copy(FRONTEND_DIR / "package.json", grading_dir)

        mock_api_proc = None
        app_proc = None
        app_port = 3000
        api_port = 3001

        try:
            # Install grading dependencies
            print(f"[{student_id}] Installing grading dependencies...")
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=grading_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            if install_result.returncode != 0:
                return {"success": False, "error": f"Failed to install grading deps: {install_result.stderr[:300]}"}

            # Install Playwright browser
            subprocess.run(
                ["npx", "playwright", "install", "chromium"],
                cwd=grading_dir,
                capture_output=True,
                timeout=120
            )

            # Install student app dependencies
            print(f"[{student_id}] Installing student app dependencies...")
            student_install = subprocess.run(
                ["npm", "install"],
                cwd=submission_root,
                capture_output=True,
                text=True,
                timeout=180
            )
            if student_install.returncode != 0:
                return {"success": False, "error": f"Failed to install student deps: {student_install.stderr[:300]}"}

            # Start mock API server
            print(f"[{student_id}] Starting mock API server...")
            mock_api_proc = subprocess.Popen(
                ["node", str(grading_dir / "mock-api-server.js"), "--mode=test", f"--port={api_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            time.sleep(2)

            # Start student app
            print(f"[{student_id}] Starting student app...")
            env = os.environ.copy()
            env["PORT"] = str(app_port)
            env["BROWSER"] = "none"
            app_proc = subprocess.Popen(
                ["npm", "start"],
                cwd=submission_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid
            )

            # Wait for app to start
            print(f"[{student_id}] Waiting for app to start...")
            app_ready = wait_for_server(f"http://localhost:{app_port}", timeout=60)
            if not app_ready:
                stderr = app_proc.stderr.read().decode() if app_proc.stderr else ""
                return {"success": False, "error": f"Student app failed to start: {stderr[:500]}"}

            # Run Playwright tests
            print(f"[{student_id}] Running Playwright tests...")
            test_result = subprocess.run(
                ["npx", "playwright", "test", "--reporter=json"],
                cwd=grading_dir,
                capture_output=True,
                text=True,
                timeout=180,
                env={
                    **os.environ,
                    "APP_URL": f"http://localhost:{app_port}",
                    "API_URL": f"http://localhost:{api_port}"
                }
            )

            # Parse test results
            result = parse_playwright_results(test_result.stdout, test_result.stderr)
            return result

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout during grading"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Cleanup processes
            if mock_api_proc:
                try:
                    os.killpg(os.getpgid(mock_api_proc.pid), signal.SIGTERM)
                except:
                    pass
            if app_proc:
                try:
                    os.killpg(os.getpgid(app_proc.pid), signal.SIGTERM)
                except:
                    pass


def find_frontend_root(base_dir: Path) -> Optional[Path]:
    """Find the actual submission root directory (contains package.json)."""
    if (base_dir / "package.json").exists():
        return base_dir

    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            if (subdir / "package.json").exists():
                return subdir
            for subsubdir in subdir.iterdir():
                if subsubdir.is_dir() and (subsubdir / "package.json").exists():
                    return subsubdir
    return None


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for a server to become available."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except:
            time.sleep(1)
    return False


def parse_playwright_results(stdout: str, stderr: str) -> dict:
    """Parse Playwright JSON output and calculate score."""
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
    test_results = []

    try:
        # Try to parse JSON from stdout
        results = json.loads(stdout)

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
                            test_results.append({
                                "test": test_title,
                                "passed": test_ok,
                                "points": points if test_ok else 0,
                                "max_points": points
                            })

        percentage = (total_score / max_score) * 100
        grade = calculate_grade(percentage)

        return {
            "success": True,
            "result": {
                "total_score": total_score,
                "max_score": max_score,
                "percentage": percentage,
                "grade": grade,
                "passed": total_score >= 60,
                "tests": test_results,
                "summary": f"Score: {total_score}/{max_score}, Grade: {grade}"
            }
        }

    except json.JSONDecodeError:
        # Couldn't parse JSON, try to extract info from stderr
        if "passed" in stderr.lower() or "failed" in stderr.lower():
            return {
                "success": False,
                "error": f"Tests completed but couldn't parse results. Output: {stderr[:500]}"
            }
        return {
            "success": False,
            "error": f"Failed to run tests: {stderr[:500]}"
        }


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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Student-ID, X-API-Key, X-Challenge')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/health':
            self.send_json({
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "challenges": ["edge-proto", "frontend"],
                "security": {
                    "sandbox_enabled": SANDBOX_ENABLED,
                    "sandbox_tool": SANDBOX_TOOL or "resource_limits",
                    "code_scanning": True
                }
            })

        elif parsed.path == '/status':
            self.send_json({
                "status": "ok",
                "stats": get_stats(),
                "config": {
                    "max_upload_size_mb": MAX_UPLOAD_SIZE / 1024 / 1024,
                    "rate_limit_per_minute": RATE_LIMIT_MAX,
                    "challenges": ["edge-proto", "frontend"]
                }
            })

        elif parsed.path == '/results':
            if not self.check_auth():
                self.send_json({"error": "Unauthorized. Provide X-API-Key header."}, 401)
                return
            challenge = parse_qs(parsed.query).get('challenge', [None])[0]
            self.send_json({"results": get_all_results(challenge)})

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
            html = self.get_web_ui()
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

            # Get headers
            student_id = self.headers.get('X-Student-ID', 'anonymous')
            student_id = ''.join(c for c in student_id if c.isalnum() or c in '_-')[:50]

            challenge = self.headers.get('X-Challenge', 'edge-proto').lower()
            if challenge not in ['edge-proto', 'frontend']:
                self.send_json({"error": "Invalid challenge. Use 'edge-proto' or 'frontend'"}, 400)
                return

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

            # Grade based on challenge type
            self.log_message(f"Grading {challenge}: {student_id} ({len(zip_data)} bytes)")

            if challenge == 'edge-proto':
                result = grade_edge_proto(zip_data, student_id)
            else:
                result = grade_frontend(zip_data, student_id)

            # Save to database
            save_submission(student_id, challenge, client_ip, result)

            # Response
            result["student_id"] = student_id
            result["challenge"] = challenge
            result["timestamp"] = datetime.now().isoformat()
            self.send_json(result, 200 if result.get("success") else 400)

        else:
            self.send_json({"error": "Not found"}, 404)

    def get_web_ui(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
    <title>Unified Grading Server</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1 { color: #333; margin-top: 0; }
        h2 { color: #555; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .form-group { margin: 20px 0; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #555; }
        input[type="text"], input[type="password"], select { padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }
        input[type="file"] { padding: 10px; }
        button { padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #1d4ed8; }
        #result { margin-top: 20px; padding: 20px; background: #1e293b; color: #e2e8f0; border-radius: 4px; white-space: pre-wrap; font-family: monospace; font-size: 13px; display: none; max-height: 500px; overflow-y: auto; }
        .info { background: #dbeafe; padding: 15px; border-radius: 4px; margin-bottom: 20px; color: #1e40af; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e5e7eb; border-radius: 4px; cursor: pointer; }
        .tab.active { background: #2563eb; color: white; }
        .challenge-info { display: none; padding: 15px; background: #f8fafc; border-radius: 4px; margin-bottom: 15px; }
        .challenge-info.active { display: block; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Unified Grading Server</h1>
        <div class="info">
            Upload your submission ZIP file to receive instant grading results.
            Select the challenge type before submitting.
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
                <label>Challenge:</label>
                <select id="challenge" onchange="updateChallengeInfo()">
                    <option value="edge-proto">Edge-Proto (Backend - Log Parsing)</option>
                    <option value="frontend">Frontend Dashboard (React)</option>
                </select>
            </div>

            <div id="edge-proto-info" class="challenge-info active">
                <strong>Edge-Proto Challenge:</strong> Submit a ZIP containing your Python or Go solution.
                <br>Expected structure: <code>edge_proto_tool/main.py</code> or compiled binary.
                <br>Scoring: A=20, B=30, C=36, D=14 (Total: 100, Pass: 60)
            </div>

            <div id="frontend-info" class="challenge-info">
                <strong>Frontend Challenge:</strong> Submit a ZIP containing your React project.
                <br>Expected: <code>package.json</code> with <code>npm start</code> script.
                <br>Your app will be tested with Playwright against the grading criteria.
            </div>

            <div class="form-group">
                <label>Submission (ZIP):</label>
                <input type="file" id="submission" accept=".zip" required>
            </div>

            <button type="submit">Submit for Grading</button>
        </form>

        <div id="result"></div>
    </div>

    <div class="card">
        <h2>API Documentation</h2>
        <pre style="background: #f1f5f9; padding: 15px; border-radius: 4px; overflow-x: auto;">
POST /submit
Headers:
  X-API-Key: your-api-key
  X-Student-ID: student_001
  X-Challenge: edge-proto | frontend
Body: ZIP file (multipart/form-data or raw)

GET /health          - Health check
GET /status          - Server statistics
GET /results         - All results (requires API key)
GET /results/:id     - Student results (requires API key)
        </pre>
    </div>

    <script>
        function updateChallengeInfo() {
            const challenge = document.getElementById('challenge').value;
            document.querySelectorAll('.challenge-info').forEach(el => el.classList.remove('active'));
            document.getElementById(challenge + '-info').classList.add('active');
        }

        document.getElementById('gradeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.textContent = 'Grading in progress... This may take a minute for frontend challenges.';

            const formData = new FormData();
            formData.append('submission', document.getElementById('submission').files[0]);

            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'X-Student-ID': document.getElementById('studentId').value,
                        'X-API-Key': document.getElementById('apiKey').value,
                        'X-Challenge': document.getElementById('challenge').value
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


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Unified Grading Server')
    parser.add_argument('--port', type=int, default=8123, help='Port to listen on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--generate-key', action='store_true', help='Generate new API key and exit')
    args = parser.parse_args()

    if args.generate_key:
        key = generate_api_key()
        save_api_key(key)
        print(f"New API key generated and saved to {API_KEY_FILE}")
        print(f"\nYour API key: {key}\n")
        print("Keep this key safe! Share it only with authorized users.")
        return

    if load_api_key() is None:
        print("No API key found. Generating one...")
        key = generate_api_key()
        save_api_key(key)
        print(f"\nYour API key: {key}\n")
        print("Save this key! You'll need it to submit.\n")

    # Initialize sandbox
    global SANDBOX_TOOL
    SANDBOX_TOOL = detect_sandbox_tool()
    print("\n[SECURITY] Sandbox Configuration:")
    print(f"  Sandbox enabled: {SANDBOX_ENABLED}")
    if SANDBOX_TOOL:
        print(f"  Sandbox tool: {SANDBOX_TOOL}")
    else:
        print(f"  Sandbox tool: None (using resource limits only)")
    print(f"  Code scanning: Enabled")
    print(f"  Resource limits: CPU={SANDBOX_MAX_CPU_TIME}s, Memory={SANDBOX_MAX_MEMORY//1024//1024}MB")
    print()

    # Check challenge directories
    challenges_ok = True
    if EDGE_PROTO_DIR.exists():
        print(f"[OK] Edge-Proto challenge: {EDGE_PROTO_DIR}")
    else:
        print(f"[WARN] Edge-Proto not found: {EDGE_PROTO_DIR}")
        challenges_ok = False

    if FRONTEND_DIR.exists():
        print(f"[OK] Frontend challenge: {FRONTEND_DIR}")
    else:
        print(f"[WARN] Frontend not found: {FRONTEND_DIR}")

    if not challenges_ok:
        print("\nWarning: Some challenge directories are missing.")
        print("Submissions for missing challenges will fail.\n")

    # Initialize database
    init_database()

    # Start server
    server = HTTPServer((args.host, args.port), GradingHandler)

    print("=" * 60)
    print("Unified Grading Server")
    print("=" * 60)
    print(f"URL:        http://{args.host}:{args.port}")
    print(f"Database:   {DATABASE_FILE}")
    print(f"API Key:    {API_KEY_FILE}")
    print("")
    print("Supported Challenges:")
    print("  - edge-proto  (Backend log parsing)")
    print("  - frontend    (React dashboard)")
    print("")
    print("Endpoints:")
    print("  GET  /           - Web UI")
    print("  GET  /health     - Health check")
    print("  GET  /status     - Stats")
    print("  GET  /results    - All results (auth required)")
    print("  POST /submit     - Submit (auth required)")
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
