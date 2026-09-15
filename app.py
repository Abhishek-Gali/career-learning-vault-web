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
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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
if (VAULT_LOCAL / "interview_history.db").exists():
    DB_PATH = VAULT_LOCAL / "interview_history.db"
else:
    DB_PATH = DATA_DIR / "web_vault.db"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

import sqlite3

# ── SQLite Database Setup ───────────────────────────────────────────────────
def init_db():
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_focus_tracker (
                    date_str TEXT PRIMARY KEY,
                    seconds_active INTEGER DEFAULT 0,
                    target_seconds INTEGER DEFAULT 7200,
                    goal_completed INTEGER DEFAULT 0,
                    last_updated_utc TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS challenge_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_id TEXT,
                    status TEXT,
                    passed_count INTEGER,
                    total_count INTEGER,
                    runtime_ms REAL,
                    submitted_at TEXT
                )
            """)
            conn.commit()
    except Exception as err:
        print(f"[DB Warning] Could not init database: {err}")

init_db()

# ── FastAPI App Setup ───────────────────────────────────────────────────────
SERVER_START_TIME = time.time()
PING_COUNT = 0

app = FastAPI(
    title="Career Learning Vault — Cloud API",
    description="Full-stack AI, Data Science & Cybersecurity Sandbox Hub",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
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

# ── API Endpoints ──────────────────────────────────────────────────────────

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
        "version": "2.0.0",
        "uptime_seconds": uptime_sec,
        "ping_count": PING_COUNT,
        "challenges_loaded": len(_CHALLENGES_CACHE),
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
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

@app.post("/api/run-code")
def run_code_endpoint(req: CodeRunRequest):
    """Executes candidate code inside an isolated subprocess against test cases."""
    ch = _CHALLENGES_CACHE.get(req.challenge_id)
    if not ch:
        raise HTTPException(status_code=404, detail=f"Challenge '{req.challenge_id}' not found.")

    report = execute_user_code(ch, req.code, run_hidden=req.run_hidden)

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO challenge_submissions (challenge_id, status, passed_count, total_count, runtime_ms, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    req.challenge_id,
                    report.get("status", "ERROR"),
                    report.get("passed_count", 0),
                    report.get("total_count", 0),
                    report.get("runtime_ms", 0.0),
                    datetime.datetime.now(datetime.timezone.utc).isoformat()
                )
            )
            conn.commit()
    except Exception as db_err:
        print(f"Error logging submission: {db_err}")

    return report

@app.get("/api/solved-challenges")
def get_solved_challenges():
    """Returns list of challenge IDs marked as passed in the database."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT challenge_id FROM challenge_submissions WHERE status = 'PASS'"
            )
            solved_ids = [row[0] for row in cursor.fetchall()]
        return {"status": "ok", "solved_ids": solved_ids, "count": len(solved_ids)}
    except Exception as err:
        return {"status": "error", "solved_ids": [], "count": 0, "detail": str(err)}

@app.post("/api/mark-solved")
def mark_solved_endpoint(req: MarkSolvedRequest):
    """Allows client to mark or unmark a challenge as solved in persistent SQLite storage."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            if req.solved:
                conn.execute(
                    "INSERT INTO challenge_submissions (challenge_id, status, passed_count, total_count, runtime_ms, submitted_at) VALUES (?, 'PASS', 1, 1, 0.0, ?)",
                    (req.challenge_id, datetime.datetime.now(datetime.timezone.utc).isoformat())
                )
            else:
                conn.execute(
                    "DELETE FROM challenge_submissions WHERE challenge_id = ?",
                    (req.challenge_id,)
                )
            conn.commit()
        return {"status": "ok", "challenge_id": req.challenge_id, "solved": req.solved}
    except Exception as err:
        return {"status": "error", "detail": str(err)}

# ── Activity-Gated Focus Timer Endpoints ────────────────────────────────────

@app.get("/api/timer")
def get_timer():
    """Returns today's active study time and weekly focus telemetry."""
    today = datetime.date.today().isoformat()
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT seconds_active, target_seconds, goal_completed FROM daily_focus_tracker WHERE date_str = ?",
                (today,)
            )
            row = cursor.fetchone()
            if row:
                sec, tgt, completed = int(row[0]), int(row[1]), bool(row[2])
            else:
                sec, tgt, completed = 0, 7200, False
                now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]
                conn.execute(
                    "INSERT INTO daily_focus_tracker (date_str, seconds_active, target_seconds, goal_completed, last_updated_utc) VALUES (?, ?, ?, ?, ?)",
                    (today, 0, 7200, 0, now_utc)
                )
                conn.commit()

            cursor.execute(
                "SELECT date_str, seconds_active, goal_completed FROM daily_focus_tracker ORDER BY date_str DESC LIMIT 7"
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
def sync_timer(req: TimerSyncRequest):
    """
    Activity-Gated Endpoint:
    Only increments seconds when the frontend confirms user activity is occurring.
    """
    if not req.is_active or req.elapsed_seconds <= 0:
        return {"status": "PAUSED_IDLE", "message": "No active study seconds accumulated."}

    added_seconds = min(req.elapsed_seconds, 120)
    today = datetime.date.today().isoformat()
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()[:19]

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seconds_active, target_seconds FROM daily_focus_tracker WHERE date_str = ?", (today,))
            row = cursor.fetchone()
            if row:
                current_sec = int(row[0]) + added_seconds
                target_sec = int(row[1])
            else:
                current_sec = added_seconds
                target_sec = 7200

            completed = 1 if current_sec >= target_sec else 0
            conn.execute("""
                INSERT INTO daily_focus_tracker (date_str, seconds_active, target_seconds, goal_completed, last_updated_utc)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date_str) DO UPDATE SET
                    seconds_active = ?,
                    goal_completed = ?,
                    last_updated_utc = ?
            """, (today, current_sec, target_sec, completed, now_utc, current_sec, completed, now_utc))
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
