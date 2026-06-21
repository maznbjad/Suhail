from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

SCHEMA = r'''
CREATE TABLE IF NOT EXISTS student_profiles (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    academic_track TEXT NOT NULL DEFAULT 'scientific',
    gender TEXT NOT NULL DEFAULT 'male',
    exam_goals_json TEXT NOT NULL DEFAULT '["qudrat","tahsili"]',
    avatar_id TEXT NOT NULL DEFAULT 'male_01',
    friend_code TEXT UNIQUE,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    diagnostic_path TEXT NOT NULL CHECK(diagnostic_path IN ('qudrat','tahsili')),
    model_key TEXT NOT NULL,
    academic_track TEXT,
    question_ids_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    submitted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_user ON diagnostic_sessions(user_id, diagnostic_path, created_at);
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    diagnostic_path TEXT NOT NULL CHECK(diagnostic_path IN ('qudrat','tahsili')),
    model_key TEXT NOT NULL,
    academic_track TEXT,
    score_percent REAL NOT NULL,
    group_scores_json TEXT NOT NULL DEFAULT '{}',
    answers_json TEXT NOT NULL DEFAULT '[]',
    elapsed_sec INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS friendship_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    receiver_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TEXT,
    UNIQUE(sender_id, receiver_code, status)
);
CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    friend_code TEXT NOT NULL,
    friend_name TEXT NOT NULL,
    avatar_id TEXT NOT NULL DEFAULT 'male_01',
    status TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_id, friend_code)
);
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id TEXT NOT NULL,
    opponent_code TEXT NOT NULL,
    template_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    question_ids_json TEXT NOT NULL DEFAULT '[]',
    owner_score INTEGER,
    owner_elapsed_sec INTEGER,
    opponent_score INTEGER,
    opponent_elapsed_sec INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted_at TEXT,
    completed_at TEXT,
    expires_at TEXT
);
CREATE TABLE IF NOT EXISTS challenge_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    selected_index INTEGER,
    is_correct INTEGER NOT NULL DEFAULT 0,
    elapsed_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(challenge_id, user_id, question_id)
);
CREATE TABLE IF NOT EXISTS learning_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    activity_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_diagnostic_user_path ON diagnostic_results(user_id, diagnostic_path, created_at);
CREATE INDEX IF NOT EXISTS idx_friend_requests_receiver ON friendship_requests(receiver_code, status);
CREATE INDEX IF NOT EXISTS idx_friendships_owner ON friendships(owner_id, status);
CREATE INDEX IF NOT EXISTS idx_challenges_owner ON challenges(owner_id, status);
CREATE INDEX IF NOT EXISTS idx_challenges_opponent ON challenges(opponent_code, status);
CREATE INDEX IF NOT EXISTS idx_activity_user_date ON learning_activity(user_id, activity_date);
'''


def friend_code_for_user(user_id: str | int) -> str:
    """Return a stable, non-sequential public code for a local user."""
    digest = hashlib.blake2s(f"suhail:{user_id}".encode("utf-8"), digest_size=5).hexdigest().upper()
    return f"SH-{digest[:6]}"


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def _add_column(connection: sqlite3.Connection, table: str, definition: str) -> None:
    name = definition.split()[0]
    if name not in _columns(connection, table):
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def ensure_social_schema(db_path: str | Path) -> None:
    """Create the Sprint 54 learning/social schema and migrate older local DBs safely."""
    with sqlite3.connect(Path(db_path)) as connection:
        connection.executescript(SCHEMA)
        # Older databases used target_exam and smaller profile/challenge tables.
        _add_column(connection, "student_profiles", "gender TEXT NOT NULL DEFAULT 'male'")
        _add_column(connection, "student_profiles", "exam_goals_json TEXT NOT NULL DEFAULT '[\"qudrat\",\"tahsili\"]'")
        _add_column(connection, "student_profiles", "friend_code TEXT")
        _add_column(connection, "friendships", "status TEXT NOT NULL DEFAULT 'accepted'")
        for definition in (
            "question_ids_json TEXT NOT NULL DEFAULT '[]'",
            "owner_elapsed_sec INTEGER",
            "opponent_elapsed_sec INTEGER",
            "accepted_at TEXT",
            "completed_at TEXT",
        ):
            _add_column(connection, "challenges", definition)
        # Backfill any profile codes created before Sprint 54.
        rows = connection.execute("SELECT user_id FROM student_profiles WHERE friend_code IS NULL OR friend_code = ''").fetchall()
        for (user_id,) in rows:
            connection.execute(
                "UPDATE student_profiles SET friend_code = ? WHERE user_id = ?",
                (friend_code_for_user(str(user_id)), str(user_id)),
            )
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_friend_code ON student_profiles(friend_code)")
        connection.commit()
