"""
lockout_demo.py — Focused demonstration of the ACCOUNT LOCKOUT control.

The main brute_force.py is a *naive* bot: it never solves the CAPTCHA, so it is
stopped by the CAPTCHA wall and the rate limiter and never even reaches the
lockout. To prove that lockout is a real, independent backstop, this script
plays a *smarter* attacker that DOES solve the arithmetic CAPTCHA (the answer
is simple maths, so a script can compute it) and paces itself to stay under the
rate limit.

Even so, after the configured number of wrong passwords the account is frozen:
the server replies 423 LOCKED and — crucially — keeps rejecting even the
CORRECT password until the lockout timer expires. That is the behaviour we want
to screenshot for the lockout feature.

Usage:
    python lockout_demo.py                 # against the protected server
    python lockout_demo.py --out lock.txt
"""

import argparse
import os
import re
import time

import requests

BASE = "http://127.0.0.1:5000"


def solve(question: str) -> str:
    """Compute the answer to a 'a + b' CAPTCHA question."""
    m = re.match(r"\s*(\d+)\s*\+\s*(\d+)\s*", question or "")
    return str(int(m.group(1)) + int(m.group(2))) if m else "0"


def attempt(sess, username, password):
    """Fetch the current CAPTCHA, solve it, and submit one login attempt."""
    q = sess.get(f"{BASE}/captcha", timeout=5).json().get("question", "")
    resp = sess.post(
        f"{BASE}/login",
        json={"username": username, "password": password, "captcha": solve(q)},
        headers={"Accept": "application/json"},
        timeout=5,
    )
    return resp.status_code, resp.json().get("message", "")


def run(username, wrong_pw, correct_pw, delay, out_path):
    sess = requests.Session()
    sess.get(BASE, timeout=5)                 # establish a session cookie
    lines = []

    def emit(t):
        print(t)
        lines.append(t)

    emit("=" * 64)
    emit(" Account-lockout demonstration (CAPTCHA-solving attacker)")
    emit(f" Target user : {username}")
    emit("=" * 64)

    locked = False
    for i in range(1, 9):
        status, msg = attempt(sess, username, wrong_pw)
        emit(f" wrong-password attempt {i}: HTTP {status} — {msg}")
        if status == 423:
            locked = True
            break
        if status == 429:                     # rate limiter tripped: wait it out
            emit("   (rate limited — pausing to isolate the lockout control)")
            time.sleep(delay * 2)
        time.sleep(delay)

    emit("-" * 64)
    # Now try the CORRECT password while (hopefully) locked.
    status, msg = attempt(sess, username, correct_pw)
    emit(f" CORRECT-password attempt while locked: HTTP {status} — {msg}")
    if locked and status == 423:
        emit(" RESULT: account LOCKED — even the valid password is refused. [PASS]")
    elif status == 200:
        emit(" RESULT: logged in — account was not locked. [check config]")
    else:
        emit(f" RESULT: blocked with HTTP {status}.")
    emit("=" * 64)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"\n[saved transcript -> {out_path}]")


def main():
    ap = argparse.ArgumentParser(description="Account-lockout demonstration")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--wrong", default="wrongpass")
    ap.add_argument("--correct", default="Summer@2025")
    ap.add_argument("--delay", type=float, default=6.5,
                    help="seconds between attempts (stay under the rate limit)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    run(args.user, args.wrong, args.correct, args.delay, args.out)


if __name__ == "__main__":
    main()
