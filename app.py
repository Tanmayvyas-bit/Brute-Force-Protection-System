"""
app.py — A small local web login server that demonstrates four defences
against dictionary / brute-force password attacks:

    1. Rate limiting      (per client IP, sliding window)   -> HTTP 429
    2. Account lockout     (per username, N strikes)          -> account frozen
    3. CAPTCHA challenge  (arithmetic, after a few failures)  -> blocks bots
    4. Logging            (file + SQLite audit table)         -> full trail

Every control is governed by config.PROTECTIONS_ENABLED so the identical
server can be launched as the vulnerable "BEFORE" target or the hardened
"AFTER" target. Passwords are stored only as salted hashes.

Endpoints
---------
GET  /            -> login form (issues a fresh CAPTCHA question in the session)
POST /login       -> process a login attempt (JSON or form) and apply defences
GET  /dashboard   -> protected page, reachable only after a correct login
GET  /captcha     -> returns the current CAPTCHA question (helper for the UI)
GET  /logout      -> clear the session

Run:
    python init_db.py           # once
    PROTECT=off python app.py   # vulnerable baseline
    PROTECT=on  python app.py   # hardened  (default)
"""

import logging
import os
import random
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime

from flask import (Flask, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash

import config

# --------------------------------------------------------------------------- #
#  Setup
# --------------------------------------------------------------------------- #
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
# Dedicated audit logger with its OWN file handler, so the Flask/Werkzeug
# access logs stay out of auth.log and the audit trail is clean.
log = logging.getLogger("auth")
log.setLevel(logging.INFO)
log.propagate = False
if not log.handlers:
    _fh = logging.FileHandler(config.LOG_FILE)
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s",
                                       datefmt="%Y-%m-%d %H:%M:%S"))
    log.addHandler(_fh)

# In-memory sliding window of request timestamps per IP (rate limiting).
_ip_hits: "defaultdict[str, deque]" = defaultdict(deque)
# How many failures each IP has produced (decides when a CAPTCHA kicks in).
_ip_failures: "defaultdict[str, int]" = defaultdict(int)


# --------------------------------------------------------------------------- #
#  Small helpers
# --------------------------------------------------------------------------- #
def db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def client_ip() -> str:
    return request.remote_addr or "unknown"


def record_attempt(ip, username, success, outcome) -> None:
    """Write one audit row to the DB and one line to the log file."""
    ts = datetime.now().isoformat(timespec="seconds")
    with db() as conn:
        conn.execute(
            "INSERT INTO login_attempts (ts, ip, username, success, outcome, protected) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, ip, username, 1 if success else 0, outcome,
             1 if config.PROTECTIONS_ENABLED else 0),
        )
    mode = "PROT" if config.PROTECTIONS_ENABLED else "OPEN"
    log.info("%-4s | ip=%-15s | user=%-12s | %s", mode, ip, username, outcome)


def new_captcha() -> None:
    """Generate a fresh arithmetic CAPTCHA and store the answer in the session."""
    a, b = random.randint(1, 9), random.randint(1, 9)
    session["captcha_q"] = f"{a} + {b}"
    session["captcha_a"] = str(a + b)


def captcha_required(ip: str) -> bool:
    return (config.PROTECTIONS_ENABLED
            and _ip_failures[ip] >= config.CAPTCHA_AFTER)


# --- Control 1: rate limiting ---------------------------------------------- #
def rate_limited(ip: str) -> bool:
    """Return True if this IP has exceeded the sliding-window request budget."""
    if not config.PROTECTIONS_ENABLED:
        return False
    now = time.time()
    hits = _ip_hits[ip]
    while hits and now - hits[0] > config.RATE_LIMIT_WINDOW:
        hits.popleft()                      # drop timestamps outside the window
    hits.append(now)
    return len(hits) > config.RATE_LIMIT_MAX


# --- Control 2: account lockout -------------------------------------------- #
def is_locked(user_row) -> bool:
    if not config.PROTECTIONS_ENABLED or user_row is None:
        return False
    return time.time() < user_row["locked_until"]


def register_failure(username: str) -> None:
    """Increment the per-account failure counter and lock it past the threshold."""
    with db() as conn:
        row = conn.execute(
            "SELECT failed_count FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return
        failed = row["failed_count"] + 1
        locked_until = 0.0
        if config.PROTECTIONS_ENABLED and failed >= config.LOCKOUT_THRESHOLD:
            locked_until = time.time() + config.LOCKOUT_DURATION
        conn.execute(
            "UPDATE users SET failed_count = ?, locked_until = ? WHERE username = ?",
            (failed, locked_until, username),
        )


def reset_failures(username: str) -> None:
    with db() as conn:
        conn.execute(
            "UPDATE users SET failed_count = 0, locked_until = 0 WHERE username = ?",
            (username,),
        )


# --------------------------------------------------------------------------- #
#  Routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    new_captcha()
    return render_template(
        "login.html",
        protected=config.PROTECTIONS_ENABLED,
        captcha_q=session.get("captcha_q"),
        show_captcha=captcha_required(client_ip()),
    )


@app.route("/captcha")
def captcha():
    return jsonify(question=session.get("captcha_q"),
                   required=captcha_required(client_ip()))


@app.route("/login", methods=["POST"])
def login():
    ip = client_ip()
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    captcha_ans = (data.get("captcha") or "").strip()

    # --- Control 1: rate limiting (checked before anything expensive) -------
    if rate_limited(ip):
        record_attempt(ip, username, False, "RATE_LIMITED")
        return _respond(ip, 429, "Too many attempts. Slow down and try again later.")

    # --- Control 3: CAPTCHA (checked before the password) -------------------
    if captcha_required(ip):
        if captcha_ans != session.get("captcha_a"):
            _ip_failures[ip] += 1
            record_attempt(ip, username, False, "CAPTCHA_FAILED")
            new_captcha()
            return _respond(ip, 403, "CAPTCHA required or incorrect.")

    with db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    # --- Control 2: account lockout ----------------------------------------
    if is_locked(user):
        wait = int(user["locked_until"] - time.time())
        record_attempt(ip, username, False, "LOCKED")
        return _respond(ip, 423, f"Account locked. Try again in ~{wait}s.")

    # --- Password check (constant-ish time via hash compare) ----------------
    if user and check_password_hash(user["password_hash"], password):
        reset_failures(username)
        _ip_failures[ip] = 0
        session["user"] = username
        record_attempt(ip, username, True, "SUCCESS")
        return _respond(ip, 200, "Login successful.", success=True)

    # Wrong username or wrong password.
    _ip_failures[ip] += 1
    if user:
        register_failure(username)
    record_attempt(ip, username, False, "BAD_PASSWORD")
    new_captcha()
    return _respond(ip, 401, "Invalid username or password.")


def _respond(ip, status, message, success=False):
    """Return JSON for API/script clients, or redirect/HTML for the browser."""
    wants_json = request.is_json or "application/json" in request.headers.get("Accept", "")
    if success and not wants_json:
        return redirect(url_for("dashboard"))
    payload = {
        "status": status,
        "message": message,
        "success": success,
        "captcha_required": captcha_required(ip),
    }
    if wants_json:
        return jsonify(payload), status
    # Browser fallback: re-render the form with the message.
    return render_template(
        "login.html",
        protected=config.PROTECTIONS_ENABLED,
        message=message,
        captcha_q=session.get("captcha_q"),
        show_captcha=captcha_required(ip),
    ), status


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=session["user"],
                           protected=config.PROTECTIONS_ENABLED)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    mode = "ENABLED (AFTER)" if config.PROTECTIONS_ENABLED else "DISABLED (BEFORE)"
    print("=" * 60)
    print("  Brute-Force Protection demo — CSL-G16 / 23ESKCS828")
    print(f"  Protections: {mode}")
    print(f"  URL: http://{config.HOST}:{config.PORT}")
    print("=" * 60)
    app.run(host=config.HOST, port=config.PORT, debug=False)
