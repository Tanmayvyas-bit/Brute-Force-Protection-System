"""
config.py — Central configuration for the Brute-Force Protection demo.

Every security control can be switched ON or OFF from one place so that the
same login server and the same attack script can be run in two modes:

    PROTECTIONS_ENABLED = False  -> "BEFORE" (vulnerable baseline, logging only)
    PROTECTIONS_ENABLED = True   -> "AFTER"  (rate limit + lockout + CAPTCHA)

The mode is read from the environment variable PROTECT so it can be toggled
without editing the file:

    PROTECT=off  python app.py      # vulnerable
    PROTECT=on   python app.py      # protected   (default)

Project : Brute-Force Protection for a Login System (CSL-G16)
Student : Tanmay Vyas (23ESKCS828)
Course  : Cyber Security Lab (7CS4-22)
"""

import os


def _flag(name: str, default: str) -> bool:
    """Read a truthy/falsy value from the environment."""
    return os.environ.get(name, default).strip().lower() in ("1", "on", "true", "yes")


# --- Master switch -----------------------------------------------------------
# Turn every protection on or off at once. Default is ON (secure).
PROTECTIONS_ENABLED = _flag("PROTECT", "on")

# --- Flask -------------------------------------------------------------------
SECRET_KEY = "demo-key-not-for-production-23ESKCS828"   # session signing (lab only)
HOST = "127.0.0.1"          # bind to localhost only -> never exposed on a network
PORT = 5000
DB_PATH = os.path.join(os.path.dirname(__file__), "security.db")
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "auth.log")

# --- Control 1: Rate limiting (per client IP) --------------------------------
# No more than RATE_LIMIT_MAX login attempts are accepted from one IP address
# inside a sliding RATE_LIMIT_WINDOW (seconds). Extra attempts get HTTP 429.
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 30          # seconds

# --- Control 2: Account lockout (per username) -------------------------------
# After LOCKOUT_THRESHOLD consecutive wrong passwords the account is frozen for
# LOCKOUT_DURATION seconds, even if the correct password is then supplied.
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = 60          # seconds (kept short so the demo is quick)

# --- Control 3: CAPTCHA challenge --------------------------------------------
# Once an IP has CAPTCHA_AFTER failures, every further attempt must also carry
# the correct answer to a simple arithmetic CAPTCHA. Automated scripts that do
# not solve it are rejected before the password is ever checked.
CAPTCHA_AFTER = 3

# --- Seed account (TEST / DUMMY credentials only — never a real password) ----
SEED_USERNAME = "admin"
SEED_PASSWORD = "Summer@2025"   # dummy lab password; also placed in the wordlist
