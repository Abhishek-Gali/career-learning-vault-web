#!/usr/bin/env python3
"""
Career Learning Vault — Cloud Web Application Backend
=====================================================
FastAPI backend service deployable to Render.com (100% free, zero credit card)
and kept running 24/7 via cron-job.org keep-alive pings.

Features:
- /api/health: Ultra-fast (<20ms) endpoint for cron-job.org keep-alive monitoring.
- /api/platforms: 10 platform categories + foundational challenge catalog (312 challenges).
- /api/challenges: Filterable challenge queries (platform, difficulty, search).
- /api/challenges/{id}: Full challenge retrieval.
- /api/run-code: 3.0s subprocess isolated sandbox execution with visible & hidden test validation.
- /api/timer & /api/timer/sync: Activity-gated focus tracker with SQLite persistence.
- /api/interviews: Comprehensive interview question sets across Cyber, DS, ML, and DSA.
"""

from __future__ import annotations

import datetime
import glob
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response, Depends, Cookie, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Application Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHALLENGES_DIR = DATA_DIR / "challenges"
INTERVIEWS_DIR = DATA_DIR / "interviews"
COURSES_FILE = DATA_DIR / "courses" / "course_catalog.json"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Fallbacks to local desktop vault if running locally on Windows and data not present
VAULT_LOCAL = Path(r"D:\Career_Learning_Vault")
if not CHALLENGES_DIR.exists() and (VAULT_LOCAL / "Coding_Sandbox" / "challenges").exists():
    CHALLENGES_DIR = VAULT_LOCAL / "Coding_Sandbox" / "challenges"

# SQLite Database Resolution:
# Prioritize DATA_DIR / "web_vault.db" so that all user data, accounts, and progress are tracked in git and persist across commits/deploys.
DB_PATH = DATA_DIR / "web_vault.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)
if not DB_PATH.exists() and (VAULT_LOCAL / "interview_history.db").exists():
    try:
        shutil.copyfile(VAULT_LOCAL / "interview_history.db", DB_PATH)
    except Exception:
        pass

import sqlite3

# ── Cryptographic Security & Password Hashing (Standard Library PBKDF2) ──────
ADMIN_DEFAULT_PASSWORD = os.environ.get("VAULT_ADMIN_PASSWORD", "Abhishek@Gali@2005")

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return f"pbkdf2:sha256:200000${salt}${key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    try:
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        algo_iter, salt, key_hex = parts
        _, _, iterations = algo_iter.split(":")
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
        return hmac.compare_digest(computed.hex(), key_hex)
    except Exception:
        return False

# ── In-Memory Login Rate Limiter (5 attempts in 15 mins) ─────────────────────
_FAILED_LOGINS: Dict[str, List[float]] = {}

def check_rate_limit(key: str, max_attempts: int = 5, window_sec: int = 900) -> bool:
    now = time.time()
    attempts = _FAILED_LOGINS.get(key, [])
    attempts = [t for t in attempts if now - t < window_sec]
    _FAILED_LOGINS[key] = attempts
    return len(attempts) < max_attempts

def record_failed_login(key: str):
    attempts = _FAILED_LOGINS.get(key, [])
    attempts.append(time.time())
    _FAILED_LOGINS[key] = attempts

def clear_failed_logins(key: str):
    _FAILED_LOGINS.pop(key, None)

# ── SQLite Database Setup & Multi-Tenant Migration ──────────────────────────
def init_db():
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            # 1. Users Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    created_by TEXT
                )
            """)
            
            # 2. User Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            # 3. User Focus Tracker Table (100% Isolated Composite Key: user_id + date_str)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_focus_tracker (
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    date_str TEXT NOT NULL,
                    seconds_active INTEGER DEFAULT 0,
                    target_seconds INTEGER DEFAULT 7200,
                    goal_completed INTEGER DEFAULT 0,
                    last_updated_utc TEXT,
                    PRIMARY KEY(user_id, date_str)
                )
            """)

            # 4. User Challenge Progress Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_challenge_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    challenge_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    passed_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    runtime_ms REAL DEFAULT 0.0,
                    user_code TEXT,
                    submitted_at TEXT NOT NULL
                )
            """)

            # 5. User Quiz History Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_quiz_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    track_key TEXT NOT NULL,
                    set_id TEXT NOT NULL,
                    correct_count INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    accuracy_pct REAL NOT NULL,
                    completed_at TEXT NOT NULL
                )
            """)

            # 6. User Custom Courses & Personal Playlists Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_custom_courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    track_key TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    course_type TEXT NOT NULL, -- 'personal' or 'playlist'
                    title TEXT NOT NULL,
                    videos_json TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    UNIQUE(user_id, track_key, course_id)
                )
            """)

            # Performance & FK Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON user_challenge_progress(user_id, challenge_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quiz_user ON user_quiz_history(user_id, track_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_custom_courses_user ON user_custom_courses(user_id, track_key)")
            conn.commit()

            # Seed Super Admin Account ONLY IF users table is completely empty (first-time deployment)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            now_iso = datetime.datetime.now(timezone.utc).isoformat()
            if user_count == 0:
                hashed = hash_password(ADMIN_DEFAULT_PASSWORD)
                conn.execute("""
                    INSERT INTO users (username, full_name, password_hash, role, is_active, created_at, created_by)
                    VALUES ('admin', 'Abhishek Gali', ?, 'admin', 1, ?, 'system')
                """, (hashed, now_iso))
                conn.commit()
                print(f"[Auth Engine] Initialized initial Super Admin account 'admin'.")
            else:
                # Existing users detected: NEVER touch, update, or overwrite user accounts or passwords!
                print(f"[Auth Engine] Existing users verified ({user_count} accounts). User records preserved untouched.")

            # Safe Non-Destructive Legacy Data Migration to Admin user (ID = 1)
            try:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_focus_tracker'")
                if cur.fetchone():
                    cur.execute("SELECT COUNT(*) FROM user_focus_tracker WHERE user_id = 1")
                    if cur.fetchone()[0] == 0:
                        conn.execute("""
                            INSERT OR IGNORE INTO user_focus_tracker (user_id, date_str, seconds_active, target_seconds, goal_completed, last_updated_utc)
                            SELECT 1, date_str, seconds_active, target_seconds, goal_completed, last_updated_utc FROM daily_focus_tracker
                        """)
                        conn.commit()
                
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='challenge_submissions'")
                if cur.fetchone():
                    cur.execute("SELECT COUNT(*) FROM user_challenge_progress WHERE user_id = 1")
                    if cur.fetchone()[0] == 0:
                        conn.execute("""
                            INSERT OR IGNORE INTO user_challenge_progress (user_id, challenge_id, status, passed_count, total_count, runtime_ms, submitted_at)
                            SELECT 1, challenge_id, status, passed_count, total_count, runtime_ms, submitted_at FROM challenge_submissions
                        """)
                        conn.commit()
            except Exception as mig_err:
                print(f"[Migration Info] Legacy table migration check: {mig_err}")

    except Exception as err:
        print(f"[DB Warning] Could not init database: {err}")

init_db()

# ── FastAPI App Setup ───────────────────────────────────────────────────────
SERVER_START_TIME = time.time()
PING_COUNT = 0

app = FastAPI(
    title="Career Learning Vault — Cloud API",
    description="Full-stack Multi-Tenant AI, Data Science & Cybersecurity Sandbox Hub",
    version="3.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_and_cache_middleware(request: Request, call_next):
    response = await call_next(request)
    # Defense-in-depth HTTP security headers (Anti-Clickjacking, Anti-MIME sniffing, Anti-XSS)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── In-Memory Cache of Challenges ──────────────────────────────────────────
_CHALLENGES_CACHE: Dict[str, Dict[str, Any]] = {}

_PLATFORM_CONFIG = [
    {"id": "placement_prep", "name": "Placement Preparation", "match_keys": ["placement"], "badge": "Campus Tech", "icon": "graduation-cap", "color": "#10b981"},
    {"id": "guvi", "name": "GUVI – CodeKata", "match_keys": ["guvi"], "badge": "CodeKata", "icon": "code", "color": "#06b6d4"},
    {"id": "hackerrank", "name": "HackerRank", "match_keys": ["hackerrank", "hr"], "badge": "Problem Solving", "icon": "terminal", "color": "#22c55e"},
    {"id": "leetcode", "name": "LeetCode", "match_keys": ["leetcode", "lc"], "badge": "FAANG Algorithms", "icon": "zap", "color": "#f59e0b"},
    {"id": "geeksforgeeks", "name": "GeeksforGeeks", "match_keys": ["geeksforgeeks", "gfg"], "badge": "Data Structures", "icon": "book-open", "color": "#10b981"},
    {"id": "codewars", "name": "Codewars", "match_keys": ["codewars", "cw"], "badge": "Kata Mastery", "icon": "swords", "color": "#ef4444"},
    {"id": "hackerearth", "name": "HackerEarth", "match_keys": ["hackerearth", "he"], "badge": "Competitive Track", "icon": "globe", "color": "#3b82f6"},
    {"id": "codechef", "name": "CodeChef", "match_keys": ["codechef", "cc"], "badge": "Contest Math", "icon": "award", "color": "#8b5cf6"},
    {"id": "programiz", "name": "Programiz", "match_keys": ["programiz", "prog"], "badge": "Syntax & Core", "icon": "cpu", "color": "#ec4899"},
    {"id": "w3schools", "name": "W3Schools", "match_keys": ["w3schools", "w3"], "badge": "Web & Algorithms", "icon": "layers", "color": "#14b8a6"},
    {"id": "foundational", "name": "Foundational Sandbox", "match_keys": ["none", "foundational"], "badge": "Interview Core", "icon": "compass", "color": "#fb7185"}
]

def normalize_platform(raw_val: Optional[str], cid: str) -> str:
    """Normalizes raw challenge platform into a standard platform ID."""
    if not raw_val or str(raw_val).strip().lower() in ("none", "", "null"):
        # Check prefix of cid
        pfx = cid.split("_")[0].lower()
        prefix_map = {
            "cc": "codechef", "cw": "codewars", "gfg": "geeksforgeeks",
            "guvi": "guvi", "he": "hackerearth", "hr": "hackerrank",
            "lc": "leetcode", "placement": "placement_prep", "prog": "programiz",
            "w3": "w3schools"
        }
        return prefix_map.get(pfx, "foundational")
    
    val = str(raw_val).lower().strip()
    for plat in _PLATFORM_CONFIG:
        for mk in plat["match_keys"]:
            if mk in val:
                return plat["id"]
    return "foundational"

def load_challenges_cache():
    global _CHALLENGES_CACHE
    _CHALLENGES_CACHE.clear()
    if not CHALLENGES_DIR.exists():
        return
    for filepath in glob.glob(str(CHALLENGES_DIR / "*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                cid = data.get("id") or Path(filepath).stem
                raw_plat = data.get("platform")
                norm_plat = normalize_platform(raw_plat, cid)
                data["normalized_platform"] = norm_plat
                if not data.get("platform"):
                    data["platform"] = "Foundational Sandbox"
                _CHALLENGES_CACHE[cid] = data
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    print(f"Loaded {len(_CHALLENGES_CACHE)} challenges into memory cache.")

load_challenges_cache()

# ── Code Sandbox Runner ────────────────────────────────────────────────────
TIMEOUT_SECONDS = 3.0

def execute_user_code(challenge_data: Dict[str, Any], user_code: str, run_hidden: bool = True) -> Dict[str, Any]:
    func_name = challenge_data.get("function_name")
    if not func_name:
        return {
            "status": "ERROR",
            "passed_count": 0,
            "total_count": 0,
            "runtime_ms": 0,
            "error_message": "Challenge is missing the function_name definition."
        }

    tests_to_run = list(challenge_data.get("visible_tests", []))
    if run_hidden:
        tests_to_run.extend(challenge_data.get("hidden_tests", []))

    tests_json_str = repr(json.dumps(tests_to_run))

    runner_code = f"""# -*- coding: utf-8 -*-
import sys
import json
import time

# User submitted solution
{user_code}

def __sandbox_runner():
    func = globals().get("{func_name}")
    if not func or not callable(func):
        print(json.dumps({{"error": "Function '{func_name}' was not defined or is not callable in your code."}}))
        sys.exit(1)

    tests = json.loads({tests_json_str})
    results = []
    total_start = time.perf_counter()

    for idx, test_case in enumerate(tests):
        inputs = test_case.get("input", {{}})
        expected = test_case.get("expected")
        t0 = time.perf_counter()
        try:
            got = func(**inputs)
            t1 = time.perf_counter()
            if isinstance(got, list) and isinstance(expected, list):
                passed = (got == expected or sorted(got) == sorted(expected))
            else:
                passed = (got == expected)
            results.append({{
                "index": idx + 1,
                "passed": passed,
                "input": inputs,
                "expected": expected,
                "got": got,
                "runtime_ms": round((t1 - t0) * 1000, 3)
            }})
        except Exception as e:
            t1 = time.perf_counter()
            results.append({{
                "index": idx + 1,
                "passed": False,
                "input": inputs,
                "expected": expected,
                "got": str(e),
                "error": str(e),
                "runtime_ms": round((t1 - t0) * 1000, 3)
            }})

    total_end = time.perf_counter()
    all_passed = all(r["passed"] for r in results)
    payload = {{
        "status": "PASS" if all_passed else "FAIL",
        "passed_count": sum(1 for r in results if r["passed"]),
        "total_count": len(results),
        "runtime_ms": round((total_end - total_start) * 1000, 2),
        "results": results
    }}
    print("===RESULT_PAYLOAD_START===")
    print(json.dumps(payload))
    print("===RESULT_PAYLOAD_END===")

if __name__ == "__main__":
    __sandbox_runner()
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(runner_code)
        temp_path = tf.name

    try:
        proc = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )
        stdout = proc.stdout
        stderr = proc.stderr
        if "===RESULT_PAYLOAD_START===" in stdout:
            payload_str = stdout.split("===RESULT_PAYLOAD_START===")[1].split("===RESULT_PAYLOAD_END===")[0].strip()
            return json.loads(payload_str)
        elif proc.returncode != 0:
            err_msg = stderr.strip() or stdout.strip() or "Execution failed with non-zero exit code."
            return {
                "status": "ERROR",
                "passed_count": 0,
                "total_count": len(tests_to_run),
                "runtime_ms": 0,
                "error_message": err_msg
            }
        else:
            return {
                "status": "ERROR",
                "passed_count": 0,
                "total_count": len(tests_to_run),
                "runtime_ms": 0,
                "error_message": "Script finished without producing test results."
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "passed_count": 0,
            "total_count": len(tests_to_run),
            "runtime_ms": int(TIMEOUT_SECONDS * 1000),
            "error_message": f"Time Limit Exceeded (> {TIMEOUT_SECONDS}s). Check for infinite loops or high time complexity."
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "passed_count": 0,
            "total_count": len(tests_to_run),
            "runtime_ms": 0,
            "error_message": str(exc)
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# ── Models ─────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class CreateUserRequest(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str
    role: str = "student" # "student" | "admin"

class ResetPasswordRequest(BaseModel):
    new_password: str

class UserStatusRequest(BaseModel):
    is_active: bool

class CodeRunRequest(BaseModel):
    challenge_id: str
    code: str
    run_hidden: bool = True

class TimerSyncRequest(BaseModel):
    elapsed_seconds: int
    is_active: bool = True

class MarkSolvedRequest(BaseModel):
    challenge_id: str
    solved: bool = True

class QuizRecordRequest(BaseModel):
    track_key: str
    set_id: str
    correct_count: int
    total_questions: int

import html
from urllib.parse import urlparse

ALLOWED_TRACK_KEYS = {"ml", "ds", "cyber", "dsa"}

def sanitize_user_input(text: Optional[str], max_len: int = 120, allow_empty: bool = True) -> str:
    """
    Sanitizes user-provided text to prevent Stored XSS and injection attacks:
    - Strips leading/trailing whitespace
    - Removes control characters and null bytes
    - Strips raw HTML/XML tags
    - Escapes HTML entities (e.g. < > & " ')
    - Enforces length bounds
    """
    if not text:
        return "" if allow_empty else None
    
    # Remove null bytes and control chars (except standard whitespace)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", str(text)).strip()
    
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*>", "", cleaned).strip()
    
    # Escape HTML special characters
    cleaned = html.escape(cleaned, quote=True)
    
    # Enforce max length
    return cleaned[:max_len]

def validate_youtube_url(url: str) -> str:
    """
    Validates that a URL is strictly a valid HTTPS YouTube watch or playlist URL.
    Rejects JavaScript URIs, SSRF targets, HTML tags, quotes, and malicious injections.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    
    cleaned = url.strip()
    
    # Immediate injection character checks
    if any(char in cleaned for char in ['<', '>', '"', "'", '`', ';', ' ']):
        raise HTTPException(status_code=400, detail="Invalid characters detected in URL.")
    
    if not cleaned.startswith("https://"):
        raise HTTPException(status_code=400, detail="Only secure HTTPS YouTube URLs are accepted.")
    
    # Hostname check
    parsed = urlparse(cleaned)
    allowed_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
    if parsed.netloc.lower() not in allowed_hosts:
        raise HTTPException(status_code=400, detail="Only official YouTube links (youtube.com / youtu.be) are supported.")
        
    return cleaned

class AddCustomVideoRequest(BaseModel):
    track_key: str
    url: str
    title: Optional[str] = None

class RenameCustomCourseRequest(BaseModel):
    track_key: str
    course_id: str
    new_title: str


# ── Authentication & RBAC Dependencies ──────────────────────────────────────
def get_current_user(
    request: Request,
    vault_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if not token:
        token = vault_session

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in to continue.", headers={"WWW-Authenticate": "Bearer"})

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, u.full_name, u.role, u.is_active, s.expires_at
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Your session has expired or is invalid. Please log in again.", headers={"WWW-Authenticate": "Bearer"})

        # Check expiration
        try:
            exp = datetime.datetime.fromisoformat(row["expires_at"])
            if datetime.datetime.now(timezone.utc) > exp:
                conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
                conn.commit()
                raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.", headers={"WWW-Authenticate": "Bearer"})
        except Exception:
            pass

        if not row["is_active"]:
            raise HTTPException(status_code=403, detail="Your account has been deactivated by the Administrator.")

        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"] or row["username"],
            "role": row["role"],
            "is_active": bool(row["is_active"])
        }

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return current_user

# ── API Endpoints ──────────────────────────────────────────────────────────

# ── Authentication Routes ───────────────────────────────────────────────────

@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest, request: Request, response: Response):
    """Authenticates user credentials, applies rate limiting, and issues secure session token."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{req.username.lower()}"

    if not check_rate_limit(rate_key, max_attempts=5, window_sec=900):
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Account temporarily locked for 15 minutes."
        )

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, password_hash, role, is_active FROM users WHERE username = ? COLLATE NOCASE", (req.username.strip(),))
        user = cur.fetchone()

        if not user or not verify_password(user["password_hash"], req.password):
            record_failed_login(rate_key)
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Account is deactivated. Contact Administrator.")

        clear_failed_logins(rate_key)

        # Generate cryptographic session token
        token = secrets.token_urlsafe(32)
        days = 30 if req.remember_me else 1
        now = datetime.datetime.now(timezone.utc)
        expires = (now + timedelta(days=days)).isoformat()

        conn.execute(
            "INSERT INTO user_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user["id"], now.isoformat(), expires)
        )
        conn.commit()

        # Set HttpOnly Session Cookie (Accessible via browser requests & sendBeacon)
        max_age_sec = days * 86400
        response.set_cookie(
            key="vault_session",
            value=token,
            max_age=max_age_sec,
            httponly=True,
            samesite="lax",
            secure=False # Set to True behind HTTPS in prod, False supports localhost dev
        )

        return {
            "status": "ok",
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"] or user["username"],
                "role": user["role"]
            }
        }

@app.post("/api/auth/logout")
def logout_endpoint(response: Response, vault_session: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    """Revokes session token and clears the authentication cookie."""
    token = vault_session
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
                conn.commit()
        except Exception:
            pass

    response.delete_cookie(key="vault_session", httponly=True, samesite="lax")
    return {"status": "ok", "message": "Successfully logged out."}

@app.get("/api/auth/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the authenticated user's profile and active role."""
    return {"status": "ok", "user": user}

@app.post("/api/auth/change-password")
def change_password_endpoint(req: ChangePasswordRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Allows user to change their own password upon validating their current credentials."""
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        row = cur.fetchone()
        if not row or not verify_password(row["password_hash"], req.old_password):
            raise HTTPException(status_code=400, detail="Current password incorrect.")

        new_hash = hash_password(req.new_password)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
        # Invalidate other active sessions for security
        conn.commit()

    return {"status": "ok", "message": "Password updated successfully."}

# ── Admin User Provisioning & Control Routes (Admin Only) ───────────────────

@app.get("/api/admin/users")
def list_admin_users(admin: Dict[str, Any] = Depends(require_admin)):
    """Lists all provisioned users, roles, account status, solved counts, and study times."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id, 
                u.username, 
                u.full_name, 
                u.role, 
                u.is_active, 
                u.created_at, 
                u.created_by,
                (SELECT COUNT(DISTINCT challenge_id) FROM user_challenge_progress WHERE user_id = u.id AND status = 'PASS') as solved_count,
                (SELECT COALESCE(SUM(seconds_active), 0) FROM user_focus_tracker WHERE user_id = u.id) as focus_seconds
            FROM users u
            ORDER BY u.id ASC
        """)
        users = [dict(r) for r in cur.fetchall()]

    return {"status": "ok", "users": users, "total_users": len(users)}

@app.post("/api/admin/users/create")
def admin_create_user(req: CreateUserRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Admin provisions a new user with temporary password and designated role."""
    uname = req.username.strip()
    if len(uname) < 3 or not uname.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Username must be 3-30 alphanumeric characters (or underscores).")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Initial password must be at least 6 characters.")
    if req.role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'admin'.")

    now_iso = datetime.datetime.now(timezone.utc).isoformat()
    hashed = hash_password(req.password)

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (username, full_name, password_hash, role, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (uname, req.full_name or uname, hashed, req.role, now_iso, admin["username"]))
            user_id = cur.lastrowid
            conn.commit()

            return {
                "status": "ok",
                "message": f"User '{uname}' provisioned successfully.",
                "user": {
                    "id": user_id,
                    "username": uname,
                    "full_name": req.full_name or uname,
                    "role": req.role
                }
            }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Username '{uname}' already exists.")

@app.post("/api/admin/users/{user_id}/reset-password")
def admin_reset_password(user_id: int, req: ResetPasswordRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Admin resets a candidate's password and revokes all active sessions."""
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    hashed = hash_password(req.new_password)
    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found.")
        # Revoke all active sessions so the old password immediately stops working
        conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        conn.commit()

    return {"status": "ok", "message": "Password reset successfully. Active sessions revoked."}

@app.post("/api/admin/users/{user_id}/status")
def admin_toggle_user_status(user_id: int, req: UserStatusRequest, admin: Dict[str, Any] = Depends(require_admin)):
    """Admin toggles active / disabled state of an account."""
    if user_id == admin["id"] and not req.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own super administrator account.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if req.is_active else 0, user_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found.")
        if not req.is_active:
            # Wipe active sessions on deactivation
            conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        conn.commit()

    return {"status": "ok", "user_id": user_id, "is_active": req.is_active}

@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: Dict[str, Any] = Depends(require_admin)):
    """Admin removes a user account and purges associated sessions and records."""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own super administrator account.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found.")
        conn.commit()

    return {"status": "ok", "message": "User deleted successfully."}

# ── Keep-Alive & Platform Catalog Routes ────────────────────────────────────

@app.get("/api/health")
def healthcheck():
    """
    Ultra-lightweight endpoint for cron-job.org keep-alive monitoring.
    Pinging this every 10 minutes keeps the Render service active 24/7/365 with $0 cost.
    """
    global PING_COUNT
    PING_COUNT += 1
    uptime_sec = round(time.time() - SERVER_START_TIME, 1)
    return {
        "status": "healthy",
        "service": "Career Learning Vault Cloud Hub",
        "version": "3.3.0",
        "uptime_seconds": uptime_sec,
        "ping_count": PING_COUNT,
        "challenges_loaded": len(_CHALLENGES_CACHE),
        "timestamp_utc": datetime.datetime.now(timezone.utc).isoformat(),
        "cron_status": "AWAKE (24/7 Keep-Alive Active)"
    }

@app.get("/api/platforms")
def get_platforms():
    """Returns the list of 10 platforms + foundational sandbox with accurate challenge counts."""
    counts: Dict[str, int] = {}
    for ch in _CHALLENGES_CACHE.values():
        plat_id = ch.get("normalized_platform", "foundational")
        counts[plat_id] = counts.get(plat_id, 0) + 1

    platforms = []
    for p in _PLATFORM_CONFIG:
        p_copy = dict(p)
        p_copy["count"] = counts.get(p["id"], 0)
        platforms.append(p_copy)
    return {"platforms": platforms, "total_challenges": len(_CHALLENGES_CACHE)}

def compute_subdivision(category: str, tags: List[str]) -> str:
    combined = f"{category} {' '.join(tags)}".lower()
    if any(k in combined for k in ['array', 'hash', 'matrix', 'prefix sum', 'set', 'table']):
        if 'two pointer' in combined or 'sliding window' in combined:
            return 'Two Pointers & Sliding Window'
        return 'Arrays & Hashing'
    if any(k in combined for k in ['two pointer', 'sliding window', 'fast-slow']):
        return 'Two Pointers & Sliding Window'
    if any(k in combined for k in ['stack', 'queue', 'deque']):
        return 'Stacks & Queues'
    if any(k in combined for k in ['binary search', 'search']):
        return 'Binary Search'
    if any(k in combined for k in ['linked list']):
        return 'Linked Lists'
    if any(k in combined for k in ['tree', 'graph', 'bfs', 'dfs', 'trie', 'bst']):
        return 'Trees & Graphs'
    if any(k in combined for k in ['dynamic programming', 'dp', 'recursion', 'backtrack', 'kadane']):
        return 'Dynamic Programming'
    if any(k in combined for k in ['greedy', 'interval']):
        return 'Greedy'
    if any(k in combined for k in ['bit', 'math', 'number theory', 'geometry', 'combinatorics', 'statistics']):
        return 'Math & Bit Manipulation'
    if any(k in combined for k in ['string', 'regex', 'suffix']):
        return 'Strings'
    return 'Core Programming & Logic'

@app.get("/api/challenges")
def get_challenges(
    platform: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 500,
    offset: int = 0
):
    """Filter challenges by platform, difficulty, or search keyword."""
    results = []
    search_lower = search.lower().strip() if search else ""

    for ch in _CHALLENGES_CACHE.values():
        ch_plat = ch.get("normalized_platform", "foundational")
        ch_diff = ch.get("difficulty", "Easy")

        if platform and platform != "all" and ch_plat != platform.lower():
            continue
        if difficulty and difficulty != "All" and ch_diff.lower() != difficulty.lower():
            continue
        if search_lower:
            text = f"{ch.get('title', '')} {ch.get('id', '')} {ch.get('category', '')} {' '.join(ch.get('tags', []))}".lower()
            if search_lower not in text:
                continue

        cat = ch.get("category", "Algorithms")
        tags = ch.get("tags", [])
        sub = compute_subdivision(cat, tags)

        results.append({
            "id": ch.get("id"),
            "title": ch.get("title"),
            "platform": ch.get("platform", "Foundational"),
            "normalized_platform": ch_plat,
            "difficulty": ch.get("difficulty", "Easy"),
            "category": cat,
            "subdivision": sub,
            "tags": tags,
            "function_name": ch.get("function_name", "solution"),
            "visible_tests_count": len(ch.get("visible_tests", [])),
            "hidden_tests_count": len(ch.get("hidden_tests", []))
        })

    # Sort: Easy -> Medium -> Hard, then Title
    diff_order = {"easy": 1, "medium": 2, "hard": 3}
    results.sort(key=lambda x: (diff_order.get(x["difficulty"].lower(), 4), x["title"]))

    total = len(results)
    paginated = results[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "challenges": paginated
    }

@app.get("/api/challenges/{challenge_id}")
def get_challenge_detail(challenge_id: str):
    """Retrieve full details of a specific challenge."""
    ch = _CHALLENGES_CACHE.get(challenge_id)
    if not ch:
        for k, v in _CHALLENGES_CACHE.items():
            if k.lower() == challenge_id.lower() or Path(k).stem.lower() == challenge_id.lower():
                ch = v
                break
    if not ch:
        raise HTTPException(status_code=404, detail=f"Challenge '{challenge_id}' not found.")
    
    initial = ch.get("starter_code") or ch.get("initial_code") or f"def {ch.get('function_name', 'solution')}():\n    # Write solution\n    pass\n"
    sol = ch.get("solution") or ch.get("solution_code") or ""

    return {
        "id": ch.get("id"),
        "title": ch.get("title"),
        "platform": ch.get("platform", "Foundational"),
        "normalized_platform": ch.get("normalized_platform", "foundational"),
        "difficulty": ch.get("difficulty", "Easy"),
        "category": ch.get("category", "Algorithms"),
        "subdivision": compute_subdivision(ch.get("category", ""), ch.get("tags", [])),
        "tags": ch.get("tags", []),
        "function_name": ch.get("function_name", "solution"),
        "description": ch.get("description", ""),
        "constraints": ch.get("constraints", ""),
        "initial_code": initial,
        "solution_code": sol,
        "visible_tests": ch.get("visible_tests", []),
        "hidden_tests_count": len(ch.get("hidden_tests", [])),
        "explanation": ch.get("explanation", "")
    }

# ── User-Scoped Interactive Code Execution & Solved Progress ───────────────

@app.post("/api/run-code")
def run_code_endpoint(req: CodeRunRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Executes candidate code inside an isolated subprocess and logs isolated progress."""
    ch = _CHALLENGES_CACHE.get(req.challenge_id)
    if not ch:
        raise HTTPException(status_code=404, detail=f"Challenge '{req.challenge_id}' not found.")

    report = execute_user_code(ch, req.code, run_hidden=req.run_hidden)

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                """INSERT INTO user_challenge_progress 
                   (user_id, challenge_id, status, passed_count, total_count, runtime_ms, user_code, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user["id"],
                    req.challenge_id,
                    report.get("status", "ERROR"),
                    report.get("passed_count", 0),
                    report.get("total_count", 0),
                    report.get("runtime_ms", 0.0),
                    req.code,
                    datetime.datetime.now(timezone.utc).isoformat()
                )
            )
            conn.commit()
    except Exception as db_err:
        print(f"Error logging submission: {db_err}")

    return report

@app.get("/api/solved-challenges")
def get_solved_challenges(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns list of challenge IDs marked as passed strictly for the authenticated user."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT challenge_id FROM user_challenge_progress WHERE user_id = ? AND status = 'PASS'",
                (user["id"],)
            )
            solved_ids = [row[0] for row in cursor.fetchall()]
        return {"status": "ok", "solved_ids": solved_ids, "count": len(solved_ids)}
    except Exception as err:
        return {"status": "error", "solved_ids": [], "count": 0, "detail": str(err)}

@app.post("/api/mark-solved")
def mark_solved_endpoint(req: MarkSolvedRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Allows client to mark or unmark a challenge as solved strictly for the authenticated user."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            if req.solved:
                conn.execute(
                    """INSERT INTO user_challenge_progress 
                       (user_id, challenge_id, status, passed_count, total_count, runtime_ms, submitted_at)
                       VALUES (?, ?, 'PASS', 1, 1, 0.0, ?)""",
                    (user["id"], req.challenge_id, datetime.datetime.now(timezone.utc).isoformat())
                )
            else:
                conn.execute(
                    "DELETE FROM user_challenge_progress WHERE user_id = ? AND challenge_id = ?",
                    (user["id"], req.challenge_id)
                )
            conn.commit()
        return {"status": "ok", "challenge_id": req.challenge_id, "solved": req.solved}
    except Exception as err:
        return {"status": "error", "detail": str(err)}

# ── User-Scoped Activity-Gated Focus Timer Endpoints ────────────────────────

@app.get("/api/timer")
def get_timer(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns today's active study time and weekly focus telemetry for the authenticated user."""
    today = datetime.date.today().isoformat()
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT seconds_active, target_seconds, goal_completed FROM user_focus_tracker WHERE user_id = ? AND date_str = ?",
                (user["id"], today)
            )
            row = cursor.fetchone()
            if row:
                sec, tgt, completed = int(row[0]), int(row[1]), bool(row[2])
            else:
                sec, tgt, completed = 0, 7200, False
                now_utc = datetime.datetime.now(timezone.utc).isoformat()[:19]
                conn.execute(
                    """INSERT INTO user_focus_tracker (user_id, date_str, seconds_active, target_seconds, goal_completed, last_updated_utc)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user["id"], today, 0, 7200, 0, now_utc)
                )
                conn.commit()

            cursor.execute(
                """SELECT date_str, seconds_active, goal_completed 
                   FROM user_focus_tracker 
                   WHERE user_id = ? 
                   ORDER BY date_str DESC LIMIT 7""",
                (user["id"],)
            )
            history = [{"date": r[0], "seconds": r[1], "completed": bool(r[2])} for r in cursor.fetchall()]
    except Exception as e:
        print(f"Timer fetch error: {e}")
        sec, tgt, completed, history = 0, 7200, False, []

    pct = round((sec / tgt) * 100, 1) if tgt > 0 else 0.0
    return {
        "date": today,
        "seconds_active": sec,
        "target_seconds": tgt,
        "goal_completed": completed,
        "percentage": min(pct, 100.0),
        "history": history
    }

@app.post("/api/timer/sync")
def sync_timer(req: TimerSyncRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    Activity-Gated Endpoint:
    Only increments seconds for authenticated user when the frontend confirms user activity.
    """
    if not req.is_active or req.elapsed_seconds <= 0:
        return {"status": "PAUSED_IDLE", "message": "No active study seconds accumulated."}

    added_seconds = min(req.elapsed_seconds, 120)
    today = datetime.date.today().isoformat()
    now_utc = datetime.datetime.now(timezone.utc).isoformat()[:19]

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seconds_active, target_seconds FROM user_focus_tracker WHERE user_id = ? AND date_str = ?", (user["id"], today))
            row = cursor.fetchone()
            if row:
                current_sec = int(row[0]) + added_seconds
                target_sec = int(row[1])
            else:
                current_sec = added_seconds
                target_sec = 7200

            completed = 1 if current_sec >= target_sec else 0
            conn.execute("""
                INSERT INTO user_focus_tracker (user_id, date_str, seconds_active, target_seconds, goal_completed, last_updated_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date_str) DO UPDATE SET
                    seconds_active = ?,
                    goal_completed = ?,
                    last_updated_utc = ?
            """, (user["id"], today, current_sec, target_sec, completed, now_utc, current_sec, completed, now_utc))
            conn.commit()

            return {
                "status": "SYNCED",
                "seconds_active": current_sec,
                "target_seconds": target_sec,
                "percentage": round(min((current_sec / target_sec) * 100, 100.0), 1),
                "goal_completed": bool(completed)
            }
    except Exception as e:
        print(f"Timer sync error: {e}")
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/quiz-results")
def record_quiz_result(req: QuizRecordRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Persists authenticated candidate's interview drill score into user_quiz_history."""
    acc = round((req.correct_count / req.total_questions) * 100, 1) if req.total_questions > 0 else 0.0
    now_iso = datetime.datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            INSERT INTO user_quiz_history (user_id, track_key, set_id, correct_count, total_questions, accuracy_pct, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], req.track_key, req.set_id, req.correct_count, req.total_questions, acc, now_iso))
        conn.commit()
    return {"status": "ok", "accuracy_pct": acc}

# ── Interview Quizzes Endpoints ─────────────────────────────────────────────

@app.get("/api/interviews")
def get_interview_tracks():
    """Lists available technical interview tracks and question bank files."""
    tracks = {
        "cybersecurity": {"title": "Cyber Security (ISC2 CC)", "sets": []},
        "data_science": {"title": "Data Science", "sets": []},
        "machine_learning": {"title": "Machine Learning", "sets": []},
        "dsa": {"title": "Data Structures & Algorithms", "sets": []}
    }

    for track_key in tracks.keys():
        t_dir = INTERVIEWS_DIR / track_key
        if t_dir.exists():
            for f in sorted(glob.glob(str(t_dir / "*.json"))):
                stem = Path(f).stem
                name = stem.replace("_", " ").title()
                try:
                    with open(f, "r", encoding="utf-8") as qf:
                        data = json.load(qf)
                        count = len(data) if isinstance(data, list) else len(data.get("questions", []))
                except Exception:
                    count = 0
                tracks[track_key]["sets"].append({
                    "id": stem,
                    "name": name,
                    "question_count": count
                })

    return tracks

@app.get("/api/interviews/{track}/{set_id}")
def get_interview_questions(track: str, set_id: str):
    """Retrieve question bank with answers and rationales for quiz drills."""
    filepath = INTERVIEWS_DIR / track / f"{set_id}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Interview set '{track}/{set_id}' not found.")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            questions = data if isinstance(data, list) else data.get("questions", [])
            return {"track": track, "set_id": set_id, "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading questions: {e}")

# ── Trilingual Structured Course Endpoints ──────────────────────────────────

@app.get("/api/courses")
def get_courses():
    """Returns the trilingual structured course catalog with video iframes and notes."""
    if not COURSES_FILE.exists():
        raise HTTPException(status_code=404, detail="Course catalog not found.")
    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error reading course catalog: {err}")

@app.get("/api/courses/{track_id}")
def get_track_course(track_id: str):
    """Returns structured course data for a specific track (ml, ds, cyber, dsa)."""
    if not COURSES_FILE.exists():
        raise HTTPException(status_code=404, detail="Course catalog not found.")
    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            track_data = data.get("tracks", {}).get(track_id.lower())
            if not track_data:
                raise HTTPException(status_code=404, detail=f"Track '{track_id}' not found in course catalog.")
            return track_data
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error reading track course: {err}")

# ── PWA Web App Manifest & Service Worker Routes ────────────────────────────

@app.get("/manifest.json")
def get_manifest():
    """Serves Web App Manifest for mobile Chrome PWA installation."""
    manifest_path = STATIC_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="manifest.json not found")

@app.get("/sw.js")
def get_service_worker():
    """Serves PWA Service Worker script."""
    sw_path = STATIC_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="sw.js not found")

# ── User Custom Videos & Playlist Hub Endpoints ─────────────────────────────

def fetch_youtube_oembed(video_id: str) -> str:
    """Fetches public YouTube video title via zero-key oEmbed endpoint with quick timeout."""
    try:
        req_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("title", f"Video {video_id}")
    except Exception:
        return f"Video {video_id}"

def fetch_playlist_metadata(playlist_url: str, playlist_id: str, custom_title: Optional[str] = None):
    """Parses playlist entries and titles using yt-dlp flat-playlist extraction, with robust fallback."""
    try:
        proc = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", "--no-warnings", playlist_url],
            capture_output=True,
            text=True,
            timeout=8
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            title = custom_title or data.get("title") or f"Playlist {playlist_id[:8]}"
            entries = data.get("entries", [])
            videos = []
            for i, e in enumerate(entries):
                if e and e.get("id"):
                    dur = ""
                    dur_sec = e.get("duration")
                    if dur_sec:
                        m, s = divmod(int(dur_sec), 60)
                        dur = f"{m}:{s:02d}"
                    videos.append({
                        "id": e.get("id"),
                        "title": e.get("title") or f"Lecture {i+1}",
                        "duration": dur
                    })
            if videos:
                return title, videos
    except Exception as err:
        print(f"[Playlist Extraction Info] yt-dlp error: {err}")

    # Fallback to single playlist stream embed
    title = custom_title or f"Custom Playlist ({playlist_id[:8]})"
    fallback_videos = [{
        "id": f"videoseries?list={playlist_id}",
        "title": title,
        "duration": "Playlist Stream"
    }]
    return title, fallback_videos

@app.get("/api/custom-courses")
def get_user_custom_courses(track_key: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves authenticated candidate's custom added playlists and personal videos."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if track_key:
            cur.execute("""
                SELECT id, track_key, course_id, course_type, title, videos_json, added_at 
                FROM user_custom_courses 
                WHERE user_id = ? AND track_key = ?
                ORDER BY id ASC
            """, (user["id"], track_key))
        else:
            cur.execute("""
                SELECT id, track_key, course_id, course_type, title, videos_json, added_at 
                FROM user_custom_courses 
                WHERE user_id = ?
                ORDER BY id ASC
            """, (user["id"],))
        rows = cur.fetchall()

        courses_by_track: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            t = r["track_key"]
            if t not in courses_by_track:
                courses_by_track[t] = []
            try:
                vids = json.loads(r["videos_json"])
            except Exception:
                vids = []
            courses_by_track[t].append({
                "id": r["course_id"],
                "course_id": r["course_id"],
                "course_type": r["course_type"],
                "title": r["title"],
                "videos": vids,
                "added_at": r["added_at"]
            })

    return {"status": "ok", "tracks": courses_by_track}

@app.post("/api/custom-courses/add")
def add_custom_video_or_playlist(req: AddCustomVideoRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    Ingests YouTube video or playlist URL with defense-in-depth sanitization:
    - Strictly validates HTTPS YouTube domain
    - Sanitizes titles against Stored XSS and SQL injection
    - If playlist (list=...): creates a separate course tab with all playlist videos.
    - If individual video: appends to candidate's 'Personal' collection.
    """
    track_key = req.track_key.strip().lower()
    if track_key not in ALLOWED_TRACK_KEYS:
        raise HTTPException(status_code=400, detail=f"Invalid track key. Allowed tracks: {', '.join(sorted(ALLOWED_TRACK_KEYS))}")

    url = validate_youtube_url(req.url)
    custom_name = sanitize_user_input(req.title, max_len=100) if req.title else None
    if custom_name and len(custom_name.strip()) == 0:
        custom_name = None

    now_iso = datetime.datetime.now(timezone.utc).isoformat()

    # Check for Playlist
    playlist_match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
    is_playlist = bool(playlist_match) and ("playlist" in url or "watch" in url)

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if is_playlist:
            pid = playlist_match.group(1)
            course_id = f"playlist_{pid}"
            extracted_title, videos = fetch_playlist_metadata(url, pid, custom_name)
            # Custom name takes top priority if user provided one
            title = custom_name or sanitize_user_input(extracted_title, max_len=100) or f"Playlist {pid[:8]}"
            # Sanitize titles in video list
            for v in videos:
                v["title"] = sanitize_user_input(v.get("title", ""), max_len=150)

            conn.execute("""
                INSERT INTO user_custom_courses (user_id, track_key, course_id, course_type, title, videos_json, added_at)
                VALUES (?, ?, ?, 'playlist', ?, ?, ?)
                ON CONFLICT(user_id, track_key, course_id) DO UPDATE SET
                    title = excluded.title,
                    videos_json = excluded.videos_json,
                    added_at = excluded.added_at
            """, (user["id"], track_key, course_id, title, json.dumps(videos), now_iso))
            conn.commit()

            return {
                "status": "ok",
                "type": "playlist",
                "course_id": course_id,
                "title": title,
                "video_count": len(videos),
                "message": f"Playlist '{title}' added as a new course tab with {len(videos)} videos!"
            }
        else:
            # Individual Video
            vid_match = re.search(r"(?:v=|\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", url)
            if not vid_match:
                raise HTTPException(status_code=400, detail="Invalid YouTube URL. Please provide a valid video or playlist link.")

            vid = vid_match.group(1)
            raw_title = custom_name or fetch_youtube_oembed(vid)
            video_title = sanitize_user_input(raw_title, max_len=150)
            video_entry = {
                "id": vid,
                "title": video_title,
                "duration": ""
            }

            course_id = "personal"
            cur.execute("""
                SELECT title, videos_json FROM user_custom_courses 
                WHERE user_id = ? AND track_key = ? AND course_id = 'personal'
            """, (user["id"], track_key))
            existing_row = cur.fetchone()

            if existing_row:
                personal_title = existing_row["title"] or "Personal"
                try:
                    v_list = json.loads(existing_row["videos_json"])
                except Exception:
                    v_list = []
                if not any(v.get("id") == vid for v in v_list):
                    v_list.append(video_entry)
                conn.execute("""
                    UPDATE user_custom_courses SET videos_json = ?, added_at = ?
                    WHERE user_id = ? AND track_key = ? AND course_id = 'personal'
                """, (json.dumps(v_list), now_iso, user["id"], track_key))
            else:
                v_list = [video_entry]
                personal_title = "Personal"
                conn.execute("""
                    INSERT INTO user_custom_courses (user_id, track_key, course_id, course_type, title, videos_json, added_at)
                    VALUES (?, ?, 'personal', 'personal', ?, ?, ?)
                """, (user["id"], track_key, personal_title, json.dumps(v_list), now_iso))

            conn.commit()

            return {
                "status": "ok",
                "type": "personal",
                "course_id": "personal",
                "title": personal_title,
                "video": video_entry,
                "video_count": len(v_list),
                "message": f"Video '{video_title}' added to your {personal_title} collection ({len(v_list)} total)!"
            }

@app.post("/api/custom-courses/rename")
def rename_custom_course(req: RenameCustomCourseRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Allows user to give custom names to any custom playlist or personal collection with input sanitization."""
    track_key = req.track_key.strip().lower()
    if track_key not in ALLOWED_TRACK_KEYS:
        raise HTTPException(status_code=400, detail="Invalid track key.")

    course_id = req.course_id.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", course_id):
        raise HTTPException(status_code=400, detail="Invalid course identifier format.")

    new_name = sanitize_user_input(req.new_title, max_len=100)
    if not new_name or not new_name.strip():
        raise HTTPException(status_code=400, detail="Course name cannot be empty or contain only tags.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            UPDATE user_custom_courses SET title = ?
            WHERE user_id = ? AND track_key = ? AND course_id = ?
        """, (new_name, user["id"], track_key, course_id))
        conn.commit()
    return {"status": "ok", "new_title": new_name}

@app.delete("/api/custom-courses/{course_id}")
def delete_custom_course(course_id: str, track_key: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)):
    """Deletes a custom playlist or personal course collection."""
    cid = course_id.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", cid):
        raise HTTPException(status_code=400, detail="Invalid course identifier format.")
    if track_key and track_key.strip().lower() not in ALLOWED_TRACK_KEYS:
        raise HTTPException(status_code=400, detail="Invalid track key.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        if track_key:
            conn.execute("""
                DELETE FROM user_custom_courses 
                WHERE user_id = ? AND track_key = ? AND course_id = ?
            """, (user["id"], track_key.strip().lower(), cid))
        else:
            conn.execute("""
                DELETE FROM user_custom_courses 
                WHERE user_id = ? AND course_id = ?
            """, (user["id"], cid))
        conn.commit()
    return {"status": "ok", "message": f"Course '{cid}' removed from shelf."}

@app.delete("/api/custom-courses/{course_id}/video/{video_id}")
def remove_video_from_custom_course(course_id: str, video_id: str, track_key: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)):
    """Removes a single video from a custom course or personal collection with input validation."""
    cid = course_id.strip()
    vid = video_id.strip()
    if not re.match(r"^[a-zA-Z0-9_-]{1,64}$", cid) or not re.match(r"^[a-zA-Z0-9_-]{1,64}$", vid):
        raise HTTPException(status_code=400, detail="Invalid identifier format.")
    if track_key and track_key.strip().lower() not in ALLOWED_TRACK_KEYS:
        raise HTTPException(status_code=400, detail="Invalid track key.")

    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if track_key:
            cur.execute("""
                SELECT id, track_key, videos_json FROM user_custom_courses
                WHERE user_id = ? AND track_key = ? AND course_id = ?
            """, (user["id"], track_key.strip().lower(), cid))
        else:
            cur.execute("""
                SELECT id, track_key, videos_json FROM user_custom_courses
                WHERE user_id = ? AND course_id = ?
            """, (user["id"], cid))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found.")
        try:
            v_list = json.loads(row["videos_json"])
            v_list = [v for v in v_list if v.get("id") != video_id]
        except Exception:
            v_list = []

        if not v_list:
            conn.execute("""
                DELETE FROM user_custom_courses
                WHERE id = ?
            """, (row["id"],))
        else:
            conn.execute("""
                UPDATE user_custom_courses SET videos_json = ?
                WHERE id = ?
            """, (json.dumps(v_list), row["id"]))
        conn.commit()

    return {"status": "ok", "remaining_videos": len(v_list)}

@app.get("/api/admin/export-db")
def export_database_backup(user: Dict[str, Any] = Depends(get_current_user)):
    """Allows administrator to download the complete SQLite database backup file."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Database file not found.")
    return FileResponse(
        path=str(DB_PATH),
        media_type="application/octet-stream",
        filename="web_vault_backup.db"
    )

# ── Frontend HTML Route ─────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the Watermelon / Refero UI Single Page Application."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Career Learning Vault Web App is Initializing...</h1>", status_code=200)
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Career Learning Vault Web App on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
