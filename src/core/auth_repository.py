from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS auth_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    iterations INTEGER NOT NULL DEFAULT 210000,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS auth_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
"""


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(db_path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_auth_schema(db_path: str | Path) -> None:
    with _connect(db_path) as connection:
        connection.executescript(AUTH_SCHEMA)
        connection.commit()


def _hash_password(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def create_user(
    db_path: str | Path,
    *,
    email: str,
    password: str,
    display_name: str,
    role: str = "student",
    iterations: int = 210_000,
) -> dict:
    email = email.strip().lower()
    if "@" not in email or len(password) < 8:
        raise ValueError("invalid_credentials")
    salt = secrets.token_bytes(16)
    digest = _hash_password(password, salt, iterations)
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """INSERT INTO auth_users
               (email, display_name, role, password_hash, password_salt, iterations)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                email,
                display_name.strip() or email.split("@")[0],
                role,
                base64.b64encode(digest).decode("ascii"),
                base64.b64encode(salt).decode("ascii"),
                iterations,
            ),
        )
        connection.commit()
        return {"id": cursor.lastrowid, "email": email, "display_name": display_name, "role": role}


def authenticate(db_path: str | Path, email: str, password: str) -> dict | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM auth_users WHERE email = ? AND active = 1",
            (email.strip().lower(),),
        ).fetchone()
    if not row:
        return None
    salt = base64.b64decode(row["password_salt"])
    expected = base64.b64decode(row["password_hash"])
    actual = _hash_password(password, salt, int(row["iterations"]))
    if not hmac.compare_digest(expected, actual):
        return None
    return {"id": row["id"], "email": row["email"], "display_name": row["display_name"], "role": row["role"]}


def issue_token(db_path: str | Path, user_id: int, ttl_hours: int = 24) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(hours=max(1, min(ttl_hours, 720)))
    with _connect(db_path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO auth_tokens (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (token_hash, user_id, expires.isoformat()),
        )
        connection.commit()
    return token


def resolve_token(db_path: str | Path, token: str) -> dict | None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as connection:
        row = connection.execute(
            """SELECT u.id, u.email, u.display_name, u.role
               FROM auth_tokens t JOIN auth_users u ON u.id = t.user_id
               WHERE t.token_hash = ? AND t.expires_at > ? AND u.active = 1""",
            (token_hash, now),
        ).fetchone()
    return dict(row) if row else None
