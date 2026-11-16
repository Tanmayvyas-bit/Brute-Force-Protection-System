"""
init_db.py — Create the SQLite database and seed one dummy test account.

Tables
------
users          : one row per account, with the salted password HASH (never the
                 plain password), the running failed-attempt counter and the
                 lockout expiry timestamp.
login_attempts : an audit log — one row for every login attempt the server
                 handled, used later for the results/analysis chapter.

Run once before starting the server:

    python init_db.py
"""

import sqlite3

from werkzeug.security import generate_password_hash

import config


def init_db() -> None:
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username        TEXT PRIMARY KEY,
            password_hash   TEXT NOT NULL,
            failed_count    INTEGER NOT NULL DEFAULT 0,
            locked_until    REAL    NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,   -- ISO timestamp
            ip          TEXT    NOT NULL,
            username    TEXT,
            success     INTEGER NOT NULL,   -- 1 = password correct
            outcome     TEXT    NOT NULL,   -- SUCCESS / BAD_PASSWORD / LOCKED / ...
            protected   INTEGER NOT NULL    -- 1 = protections were enabled
        )
    """)

    # Seed / reset the single dummy account with a FRESH hash and clean counters.
    pw_hash = generate_password_hash(config.SEED_PASSWORD)
    cur.execute("DELETE FROM users WHERE username = ?", (config.SEED_USERNAME,))
    cur.execute(
        "INSERT INTO users (username, password_hash, failed_count, locked_until) "
        "VALUES (?, ?, 0, 0)",
        (config.SEED_USERNAME, pw_hash),
    )

    conn.commit()
    conn.close()
    print(f"[init_db] Database ready at {config.DB_PATH}")
    print(f"[init_db] Seeded test account: {config.SEED_USERNAME} / {config.SEED_PASSWORD}")
    print("[init_db] (dummy lab credentials — not a real password)")


if __name__ == "__main__":
    init_db()
