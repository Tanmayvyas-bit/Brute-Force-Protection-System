# Brute-Force Protection for a Login System (CSL-G16)

**Cyber Security Lab (7CS4-22) — Mini Project** · Experiment 3: Dictionary & Brute-Force Attack
**Student:** Tanmay Vyas · **Roll No.:** 23ESKCS828 · **Batch:** CSL-G16

A small local web login system (Flask) hardened against automated password
guessing with **four layered defences** — per-IP **rate limiting**, per-account
**lockout**, a **CAPTCHA** challenge, and full **logging** — plus an attacker
script that runs a dictionary/brute-force attack against it **before** and
**after** the defences are enabled.

> **Ethical use only.** The server binds to `127.0.0.1` (localhost). Run the
> attack *only* against this local server, using the dummy test account. Never
> point it at any system you do not own. Misuse is an offence under the IT Act,
> 2000 (Sec. 43, 66).

---

## 1. Requirements

```bash
python3 -m pip install -r requirements.txt
```

(Flask, Werkzeug, requests. `python-docx` is only needed to regenerate the report.)

## 2. Quick start — reproduce the whole experiment

One command initialises the DB, runs the server with protections **off** then
**on**, launches the attack against each, and saves all transcripts to
`results/`:

```bash
bash run_demo.sh
```

Expected: the attack **cracks** the password with protections off, and is
**blocked** (429 / 403 / 423) with protections on.

## 3. Run the pieces manually

```bash
python3 init_db.py                 # create DB + seed dummy account

PROTECT=off python3 app.py         # vulnerable "BEFORE" target  (http://127.0.0.1:5000)
PROTECT=on  python3 app.py         # hardened  "AFTER"  target   (default)

python3 attack/brute_force.py      # dictionary attack (naive bot)
python3 attack/lockout_demo.py     # CAPTCHA-solving bot -> hits the lockout wall
```

Open `http://127.0.0.1:5000` in a browser to use the login form.
Test account: **`admin` / `Summer@2025`** (dummy lab credentials).

## 4. The four controls (all toggled by `PROTECT`)

| # | Control        | Scope        | Trigger                     | Response |
|---|----------------|--------------|-----------------------------|----------|
| 1 | Rate limiting  | per client IP| > 5 attempts / 30 s         | HTTP 429 |
| 2 | Account lockout| per username | 5 consecutive failures      | HTTP 423 (60 s freeze) |
| 3 | CAPTCHA        | per client IP| after 3 failures            | HTTP 403 until solved |
| 4 | Logging        | every attempt| always                      | `logs/auth.log` + SQLite audit table |

Tune the thresholds in `config.py`.

## 5. Project layout

```
config.py            Central config + master PROTECT switch
app.py               Flask login server implementing the four controls
init_db.py           Creates security.db and seeds the dummy account
templates/           login.html, dashboard.html
static/style.css     Styling
attack/
  brute_force.py     Dictionary/brute-force attacker (before vs after)
  lockout_demo.py    Focused account-lockout demonstration
  wordlist.txt       Small password wordlist (contains the dummy password)
run_demo.sh          One-command end-to-end reproduction
results/             Attack transcripts (generated)
screenshots/         UI screenshots used in the report
report/
  generate_report.py Builds the formatted .docx report from the real output
  23ESKCS828_TanmayVyas_CSL-G16_Report.docx
```

## 6. Regenerate the report

```bash
python3 report/generate_report.py
```

It reads the live source files, the `results/` transcripts and the
`screenshots/`, so the report always matches the working code.
The Table of Contents page numbers are indicative; open the `.docx` in Word and
press **Ctrl+A → F9** if you add content and want them recomputed.
