from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    exam TEXT NOT NULL,
    category TEXT NOT NULL,
    skill TEXT,
    subject TEXT,
    unit TEXT,
    difficulty TEXT,
    payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_exam ON questions(exam);
CREATE INDEX IF NOT EXISTS idx_questions_skill ON questions(skill);
CREATE INDEX IF NOT EXISTS idx_questions_subject_unit ON questions(subject, unit);
"""


def build_sqlite(json_path: str | Path, db_path: str | Path) -> int:
    questions = json.loads(Path(json_path).read_text(encoding="utf-8"))
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM questions")
        conn.executemany(
            """INSERT INTO questions
               (id, exam, category, skill, subject, unit, difficulty, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    str(q.get("id", "")), str(q.get("exam", "")),
                    str(q.get("category", "")), str(q.get("skill", "")),
                    str(q.get("subject", "")), str(q.get("unit", "")),
                    str(q.get("difficulty", "")),
                    json.dumps(q, ensure_ascii=False, separators=(",", ":")),
                )
                for q in questions
            ],
        )
        conn.commit()
    return len(questions)


def fetch_questions(db_path: str | Path, exam: str | None = None, limit: int = 50) -> list[dict]:
    sql = "SELECT payload_json FROM questions"
    params: list[object] = []
    if exam:
        sql += " WHERE exam = ?"
        params.append(exam)
    sql += " LIMIT ?"
    params.append(max(1, min(limit, 500)))
    with sqlite3.connect(db_path) as conn:
        return [json.loads(row[0]) for row in conn.execute(sql, params)]
