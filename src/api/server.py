from __future__ import annotations

import gzip
import json
import os
import secrets
import sqlite3
import time
import uuid
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.core.app_config import (
    ADMIN_SETTINGS_PATH,
    invalidate_config_cache,
    load_admin_settings,
    load_avatars,
    load_challenge_templates,
    load_feature_flags,
    load_score_models,
)
from src.core.auth_repository import (
    authenticate,
    create_user,
    ensure_auth_schema,
    issue_token,
    resolve_token,
)
from src.core.challenge_repository import ensure_social_schema, friend_code_for_user

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "suhail_learning.db"
SUMMARIES_PATH = ROOT / "data" / "smart_summaries.json"
RELEASE = "114.0.0"
ALLOWED_EXAMS = {"قدرات كمي", "قدرات لفظي", "تحصيلي"}
AUTH_WINDOW_SEC = 60
AUTH_MAX_ATTEMPTS = 10
_AUTH_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)


def _bounded_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(value or default)))
    except (TypeError, ValueError):
        return default


def _connect(*, query_only: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    if query_only:
        connection.execute("PRAGMA query_only = ON")
    else:
        connection.execute("PRAGMA foreign_keys = ON")
    return connection


@lru_cache(maxsize=1)
def _summaries() -> list[dict[str, Any]]:
    try:
        payload = json.loads(SUMMARIES_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _question_query() -> tuple[str, list[Any]]:
    filters: list[str] = []
    params: list[Any] = []
    for column in ("exam", "category", "skill", "subject", "unit", "difficulty"):
        value = (request.args.get(column) or "").strip()
        if value:
            filters.append(f"{column} = ?")
            params.append(value)
    if (request.args.get("release_eligible") or "").lower() in {"1", "true", "yes"}:
        filters.append("json_extract(payload_json, '$.release_eligible') = 1")
    diagnostic = (request.args.get("diagnostic") or "").lower()
    if diagnostic in {"1", "true", "yes"}:
        filters.append("json_extract(payload_json, '$.diagnostic') = 1")
    sql = "SELECT payload_json FROM questions"
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([
        _bounded_int(request.args.get("limit"), 50, 1, 200),
        _bounded_int(request.args.get("offset"), 0, 0, 1_000_000),
    ])
    return sql, params


def _fetch_diagnostic(exam: str, count: int, subject: str | None = None) -> list[dict[str, Any]]:
    where = ["exam = ?"]
    params: list[Any] = [exam]
    if subject:
        where.append("subject = ?")
        params.append(subject)
    sql = f"""SELECT payload_json FROM questions
              WHERE {' AND '.join(where)}
              ORDER BY json_extract(payload_json, '$.diagnostic') DESC, id
              LIMIT ?"""
    params.append(max(0, int(count)))
    with _connect(query_only=True) as connection:
        return [json.loads(row[0]) for row in connection.execute(sql, params).fetchall()]


def _public_question(question: dict[str, Any]) -> dict[str, Any]:
    """Return the fields required to render a question without leaking its answer."""
    hidden = {
        "correct", "answer", "explain", "explanation", "release_eligible", "editorial_status",
        "rights_status", "source", "source_url", "review_notes",
    }
    return {key: value for key, value in question.items() if key not in hidden}

def _ensure_profile_for_user(connection: sqlite3.Connection, user: dict[str, Any]) -> sqlite3.Row:
    """Create the minimal student profile required for friends/challenges."""
    user_id = str(user["id"])
    row = connection.execute(
        """SELECT p.*, u.username FROM student_profiles p
           LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = p.user_id
           WHERE p.user_id = ?""",
        (user_id,),
    ).fetchone()
    if row:
        return row
    gender = "male"
    connection.execute(
        """INSERT INTO student_profiles
           (user_id, display_name, academic_track, gender, exam_goals_json, avatar_id, friend_code, updated_at)
           VALUES (?, ?, 'scientific', ?, '["qudrat","tahsili"]', ?, ?, CURRENT_TIMESTAMP)""",
        (
            user_id,
            str(user.get("display_name") or user.get("username") or "طالب سهيل"),
            gender,
            "male_02",
            friend_code_for_user(user_id),
        ),
    )
    return connection.execute(
        """SELECT p.*, u.username FROM student_profiles p
           LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = p.user_id
           WHERE p.user_id = ?""",
        (user_id,),
    ).fetchone()


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _group_member_profile(connection: sqlite3.Connection, friend_code: str) -> sqlite3.Row | None:
    return connection.execute(
        """SELECT p.user_id, p.display_name, p.avatar_id, p.friend_code, u.username
           FROM student_profiles p
           LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = p.user_id
           WHERE p.friend_code = ?""",
        (friend_code,),
    ).fetchone()


def _advance_group_if_expired(connection: sqlite3.Connection, room_id: str) -> sqlite3.Row | None:
    """Advance one expired question using server time; callers hold a write transaction."""
    room = connection.execute("SELECT * FROM group_challenges WHERE id = ?", (room_id,)).fetchone()
    if not room or room["status"] != "active":
        return room
    started = _parse_utc(room["question_started_at"])
    if not started:
        return room
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    if elapsed < int(room["question_time_sec"] or 30):
        return room
    next_index = int(room["current_index"] or 0) + 1
    if next_index >= int(room["question_count"] or 0):
        connection.execute(
            """UPDATE group_challenges SET status='completed', current_index=?, completed_at=?,
               last_event='timeout', last_winner_user_id=NULL, last_winner_name=NULL,
               last_winner_elapsed_ms=NULL WHERE id=?""",
            (next_index, datetime.now(timezone.utc).isoformat(), room_id),
        )
    else:
        connection.execute(
            """UPDATE group_challenges SET current_index=?, question_started_at=?,
               last_event='timeout', last_winner_user_id=NULL, last_winner_name=NULL,
               last_winner_elapsed_ms=NULL WHERE id=?""",
            (next_index, datetime.now(timezone.utc).isoformat(), room_id),
        )
    return connection.execute("SELECT * FROM group_challenges WHERE id = ?", (room_id,)).fetchone()


def _group_state_payload(connection: sqlite3.Connection, room: sqlite3.Row, user_id: str) -> dict[str, Any]:
    member = connection.execute(
        "SELECT * FROM group_challenge_members WHERE room_id = ? AND user_id = ?",
        (room["id"], user_id),
    ).fetchone()
    if not member:
        raise PermissionError("group_challenge_access_denied")
    members = connection.execute(
        """SELECT user_id, friend_code, display_name, username, status, score, correct_count,
                  total_response_ms, joined_at
           FROM group_challenge_members WHERE room_id = ?
           ORDER BY score DESC, total_response_ms ASC, display_name ASC""",
        (room["id"],),
    ).fetchall()
    question_ids = json.loads(room["question_ids_json"] or "[]")
    current_index = int(room["current_index"] or 0)
    current_question: dict[str, Any] | None = None
    already_answered = False
    if room["status"] == "active" and current_index < len(question_ids):
        question_id = str(question_ids[current_index])
        qrow = connection.execute("SELECT payload_json FROM questions WHERE id = ?", (question_id,)).fetchone()
        if qrow:
            current_question = _public_question(json.loads(qrow[0]))
        already_answered = bool(connection.execute(
            "SELECT 1 FROM group_challenge_answers WHERE room_id = ? AND question_index = ? AND user_id = ?",
            (room["id"], current_index, user_id),
        ).fetchone())
    now = datetime.now(timezone.utc)
    started = _parse_utc(room["question_started_at"])
    elapsed_ms = max(0, int((now - started).total_seconds() * 1000)) if started else 0
    duration_ms = int(room["question_time_sec"] or 30) * 1000
    return {
        "id": room["id"],
        "owner_id": room["owner_id"],
        "exam": room["exam"],
        "status": room["status"],
        "question_count": int(room["question_count"] or 0),
        "question_time_sec": int(room["question_time_sec"] or 30),
        "current_index": current_index,
        "current_number": min(current_index + 1, int(room["question_count"] or 0)),
        "question": current_question,
        "remaining_ms": max(0, duration_ms - elapsed_ms) if room["status"] == "active" else 0,
        "server_time": now.isoformat(),
        "question_started_at": room["question_started_at"],
        "last_event": room["last_event"],
        "last_winner_user_id": room["last_winner_user_id"],
        "last_winner_name": room["last_winner_name"],
        "last_winner_elapsed_ms": room["last_winner_elapsed_ms"],
        "already_answered": already_answered,
        "is_owner": str(room["owner_id"]) == str(user_id),
        "my_status": member["status"],
        "my_user_id": str(user_id),
        "members": [dict(row) for row in members],
    }


def _score_diagnostic_items(
    items: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    *,
    path: str,
    model_key: str,
) -> dict[str, Any]:
    selected_by_id = {
        str(item.get("question_id", "")): item.get("selected_index")
        for item in answers if isinstance(item, dict)
    }
    groups: dict[str, dict[str, int | float]] = {}
    correct_total = 0
    for question in items:
        question_id = str(question.get("id", ""))
        selected = selected_by_id.get(question_id)
        is_correct = isinstance(selected, int) and selected == question.get("correct")
        correct_total += int(is_correct)
        group_name = str(question.get("exam")) if path == "qudrat" else str(question.get("subject") or "تحصيلي")
        group = groups.setdefault(group_name, {"total": 0, "correct": 0, "percent": 0})
        group["total"] = int(group["total"]) + 1
        group["correct"] = int(group["correct"]) + int(is_correct)
    for group in groups.values():
        group["percent"] = round(int(group["correct"]) / max(1, int(group["total"])) * 100)

    model = load_score_models().get("models", {}).get(model_key, {})
    if path == "qudrat":
        weighted = (
            float(groups.get("قدرات كمي", {}).get("percent", 0)) * float(model.get("quant_weight", 0.5))
            + float(groups.get("قدرات لفظي", {}).get("percent", 0)) * float(model.get("verbal_weight", 0.5))
        )
    else:
        weighted = sum(
            float(groups.get(subject, {}).get("percent", 0)) * float(model.get(weight_key, 0.25))
            for subject, weight_key in (
                ("رياضيات", "math_weight"), ("فيزياء", "physics_weight"),
                ("كيمياء", "chemistry_weight"), ("الأحياء وعلم البيئة", "biology_weight"),
            )
        )
    return {
        "total": len(items),
        "correct": correct_total,
        "raw_percent": round(correct_total / max(1, len(items)) * 100),
        "weighted_percent": round(max(0, min(100, weighted))),
        "groups": groups,
    }


def _public_settings() -> dict[str, Any]:
    settings = load_admin_settings()
    return {
        "release": RELEASE,
        "general": settings.get("general", {}),
        "learning": settings.get("learning", {}),
        "diagnostic": settings.get("diagnostic", {}),
        "streak": settings.get("streak", {}),
        "challenges": settings.get("challenges", {}),
        "notifications": settings.get("notifications", {}),
        "features": settings.get("features", {}),
        "performance": settings.get("performance", {}),
        "navigation": settings.get("navigation", {}),
        "feature_flags": load_feature_flags().get("flags", {}),
    }


def _admin_authorized() -> bool:
    expected = os.environ.get("SUHAIL_ADMIN_TOKEN", "").strip()
    provided = request.headers.get("X-Suhail-Admin-Token", "").strip()
    return bool(expected and provided and secrets_compare(expected, provided))


def secrets_compare(a: str, b: str) -> bool:
    import hmac
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _bearer_user() -> dict | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return resolve_token(DB_PATH, header[7:].strip())


def _require_user() -> tuple[dict | None, Any | None]:
    user = _bearer_user()
    if not user:
        return None, (jsonify({"error": "authentication_required"}), 401)
    return user, None


def _rate_limited(scope: str) -> bool:
    identity = f"{scope}:{request.remote_addr or 'unknown'}"
    now = time.time()
    bucket = _AUTH_ATTEMPTS[identity]
    while bucket and now - bucket[0] > AUTH_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= AUTH_MAX_ATTEMPTS:
        return True
    bucket.append(now)
    return False


def _profile_payload(row: sqlite3.Row) -> dict[str, Any]:
    goals = json.loads(row["exam_goals_json"] or "[]")
    return {
        "user_id": row["user_id"],
        "display_name": row["display_name"],
        "username": row["username"] if "username" in row.keys() else None,
        "academic_track": row["academic_track"],
        "gender": row["gender"] if "gender" in row.keys() else "male",
        "exam_goals": goals,
        "avatar_id": row["avatar_id"],
        "friend_code": row["friend_code"] or friend_code_for_user(row["user_id"]),
        "updated_at": row["updated_at"],
    }


def _server_streak(user_id: str) -> dict[str, Any]:
    with _connect(query_only=True) as connection:
        rows = connection.execute(
            "SELECT DISTINCT activity_date FROM learning_activity WHERE user_id = ? ORDER BY activity_date DESC LIMIT 500",
            (user_id,),
        ).fetchall()
    dates = {date.fromisoformat(row[0]) for row in rows}
    today_value = datetime.now(timezone.utc).date()
    has_today = today_value in dates
    cursor = today_value if has_today else today_value - timedelta(days=1)
    count = 0
    while cursor in dates and count < 500:
        count += 1
        cursor -= timedelta(days=1)
    now = datetime.now(timezone.utc)
    midnight = datetime.combine(today_value + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    seconds_left = max(0, int((midnight - now).total_seconds()))
    rescue_hours = int(load_admin_settings().get("streak", {}).get("rescue_window_hours", 6))
    return {
        "count": count,
        "has_today": has_today,
        "risk": (not has_today and count > 0 and seconds_left <= rescue_hours * 3600),
        "seconds_left": seconds_left,
        "timezone": "UTC",
        "server_time": now.isoformat(),
    }


def create_app() -> Flask:
    ensure_social_schema(DB_PATH)
    ensure_auth_schema(DB_PATH)
    app = Flask(__name__)
    app.json.ensure_ascii = False
    configured_origins = os.environ.get("SUHAIL_ALLOWED_ORIGINS", "").strip()
    allowed_origins: str | list[str] = [x.strip() for x in configured_origins.split(",") if x.strip()] if configured_origins else "*"
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "suhail-api", "release": RELEASE, "database": DB_PATH.exists()})

    @app.get("/api/v1/config/public")
    def public_config():
        return jsonify(_public_settings())

    @app.post("/api/v1/auth/register")
    def auth_register():
        if _rate_limited("register"):
            return jsonify({"error": "rate_limited"}), 429
        payload = request.get_json(silent=True) or {}
        try:
            user = create_user(
                DB_PATH,
                email=str(payload.get("email", "")),
                password=str(payload.get("password", "")),
                display_name=str(payload.get("display_name", "")),
                username=str(payload.get("username", "")),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "email_exists"}), 409
        except ValueError:
            return jsonify({"error": "invalid_credentials"}), 400
        with _connect() as connection:
            _ensure_profile_for_user(connection, user)
            connection.commit()
        token = issue_token(DB_PATH, int(user["id"]))
        return jsonify({"user": user, "token": token}), 201

    @app.post("/api/v1/auth/login")
    def auth_login():
        if _rate_limited("login"):
            return jsonify({"error": "rate_limited"}), 429
        payload = request.get_json(silent=True) or {}
        user = authenticate(DB_PATH, str(payload.get("email", "")), str(payload.get("password", "")))
        if not user:
            return jsonify({"error": "invalid_credentials"}), 401
        with _connect() as connection:
            _ensure_profile_for_user(connection, user)
            connection.commit()
        token = issue_token(DB_PATH, int(user["id"]))
        return jsonify({"user": user, "token": token})

    @app.get("/api/v1/auth/me")
    def auth_me():
        user, error = _require_user()
        return error or jsonify({"user": user})

    @app.get("/api/v1/profile")
    def profile_get():
        user, error = _require_user()
        if error:
            return error
        with _connect(query_only=True) as connection:
            row = connection.execute(
                """SELECT p.*, u.username
                   FROM student_profiles p
                   LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = p.user_id
                   WHERE p.user_id = ?""",
                (str(user["id"]),),
            ).fetchone()
        if not row:
            return jsonify({"profile": None})
        return jsonify({"profile": _profile_payload(row)})

    @app.put("/api/v1/profile")
    def profile_put():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        goals = [x for x in payload.get("exam_goals", []) if x in {"qudrat", "tahsili"}]
        if not goals:
            return jsonify({"error": "at_least_one_exam_goal_required"}), 400
        academic_track = str(payload.get("academic_track", "scientific"))
        if academic_track not in {"scientific", "literary"}:
            return jsonify({"error": "invalid_academic_track"}), 400
        gender = str(payload.get("gender", "male"))
        if gender not in {"male", "female"}:
            return jsonify({"error": "invalid_gender"}), 400
        avatar_id = str(payload.get("avatar_id") or ("female_01" if gender == "female" else "male_02"))
        avatar_catalog = {str(item.get("id")): item for item in load_avatars().get("items", [])}
        avatar = avatar_catalog.get(avatar_id)
        avatar_gender = str((avatar or {}).get("gender_key") or avatar_id.split("_", 1)[0])
        if not avatar or avatar_gender != gender or avatar.get("enabled") is False:
            return jsonify({"error": "avatar_gender_mismatch"}), 400
        with _connect() as connection:
            connection.execute(
                """INSERT INTO student_profiles
                   (user_id, display_name, academic_track, gender, exam_goals_json, avatar_id, friend_code, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(user_id) DO UPDATE SET
                     display_name=excluded.display_name,
                     academic_track=excluded.academic_track,
                     gender=excluded.gender,
                     exam_goals_json=excluded.exam_goals_json,
                     avatar_id=excluded.avatar_id,
                     updated_at=CURRENT_TIMESTAMP""",
                (
                    str(user["id"]),
                    str(payload.get("display_name") or user["display_name"]),
                    academic_track,
                    gender,
                    json.dumps(goals, ensure_ascii=False),
                    avatar_id,
                    friend_code_for_user(str(user["id"])),
                ),
            )
            connection.commit()
            row = connection.execute("SELECT * FROM student_profiles WHERE user_id = ?", (str(user["id"]),)).fetchone()
        return jsonify({"profile": _profile_payload(row)})

    @app.get("/api/v1/avatars")
    def avatars():
        return jsonify(load_avatars())

    @app.get("/api/v1/challenges/templates")
    def challenge_templates():
        return jsonify(load_challenge_templates())

    @app.get("/api/v1/scoring/models")
    def scoring_models():
        return jsonify(load_score_models())

    @app.get("/api/v1/catalog")
    def catalog():
        with _connect(query_only=True) as connection:
            rows = connection.execute(
                """SELECT exam, category, subject, COUNT(*) AS total,
                          SUM(CASE WHEN json_extract(payload_json, '$.release_eligible') = 1 THEN 1 ELSE 0 END) AS release_total
                   FROM questions GROUP BY exam, category, subject
                   ORDER BY exam, category, subject"""
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.get("/api/v1/questions")
    def questions():
        user, error = _require_user()
        if error:
            return error
        sql, params = _question_query()
        with _connect(query_only=True) as connection:
            rows = connection.execute(sql, params).fetchall()
        items = [json.loads(row[0]) for row in rows]
        include_answers = (request.args.get("include_answers") or "").lower() in {"1", "true", "yes"}
        if include_answers and not _admin_authorized():
            return jsonify({"error": "admin_token_required_for_answers"}), 401
        public_items = items if include_answers else [_public_question(item) for item in items]
        return jsonify({"items": public_items, "count": len(public_items), "answers_included": include_answers})

    @app.post("/api/v1/questions/grade")
    def questions_grade():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        answers = payload.get("answers") if isinstance(payload.get("answers"), list) else []
        answers = answers[:100]
        question_ids = [str(item.get("question_id", "")) for item in answers if isinstance(item, dict)]
        if not question_ids:
            return jsonify({"error": "answers_required"}), 400
        placeholders = ",".join("?" for _ in question_ids)
        with _connect(query_only=True) as connection:
            rows = connection.execute(
                f"SELECT id, payload_json FROM questions WHERE id IN ({placeholders})", question_ids
            ).fetchall()
        by_id = {str(row["id"]): json.loads(row["payload_json"]) for row in rows}
        results = []
        correct_total = 0
        for submitted in answers:
            qid = str(submitted.get("question_id", ""))
            question = by_id.get(qid)
            if not question:
                continue
            selected = submitted.get("selected_index")
            is_correct = isinstance(selected, int) and selected == question.get("correct")
            correct_total += int(is_correct)
            results.append({
                "question_id": qid,
                "selected_index": selected,
                "is_correct": is_correct,
                "correct_index": question.get("correct"),
                "explanation": question.get("explanation", ""),
                "skill": question.get("skill", ""),
            })
        return jsonify({
            "results": results,
            "total": len(results),
            "correct": correct_total,
            "percent": round(correct_total / max(1, len(results)) * 100),
        })

    @app.get("/api/v1/diagnostic")
    def diagnostic():
        user, error = _require_user()
        if error:
            return error
        path = (request.args.get("path") or "").strip().lower()
        requested_track = (request.args.get("track") or "").strip().lower()
        settings = load_admin_settings().get("diagnostic", {})
        if path not in {"qudrat", "tahsili"}:
            return jsonify({"error": "path_must_be_qudrat_or_tahsili", "separate_records": True}), 400

        with _connect(query_only=True) as connection:
            profile = connection.execute(
                "SELECT academic_track FROM student_profiles WHERE user_id = ?", (str(user["id"]),)
            ).fetchone()
        stored_track = str(profile["academic_track"]) if profile else "scientific"
        track = requested_track or stored_track
        items: list[dict[str, Any]] = []
        model = "tahsili_common"
        if path == "qudrat":
            if track not in {"scientific", "literary"}:
                return jsonify({"error": "invalid_track"}), 400
            model = "qudrat_literary" if track == "literary" else "qudrat_scientific"
            config = settings.get(model, {})
            items.extend(_fetch_diagnostic("قدرات كمي", int(config.get("quant", 6))))
            items.extend(_fetch_diagnostic("قدرات لفظي", int(config.get("verbal", 6))))
        else:
            # Tahsili is intentionally common. requested_track is ignored and never persisted.
            track = None
            config = settings.get("tahsili_common", {})
            for subject, key in (("رياضيات", "math"), ("فيزياء", "physics"), ("كيمياء", "chemistry"), ("الأحياء وعلم البيئة", "biology")):
                items.extend(_fetch_diagnostic("تحصيلي", int(config.get(key, 3)), subject))

        session_id = secrets.token_urlsafe(20)
        expires = datetime.now(timezone.utc) + timedelta(hours=2)
        with _connect() as connection:
            connection.execute(
                """INSERT INTO diagnostic_sessions
                   (id, user_id, diagnostic_path, model_key, academic_track, question_ids_json, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id, str(user["id"]), path, model, track,
                    json.dumps([str(item.get("id", "")) for item in items]), expires.isoformat(),
                ),
            )
            connection.commit()
        return jsonify({
            "items": [_public_question(item) for item in items],
            "count": len(items),
            "available": True,
            "path": path,
            "track_used": track if path == "qudrat" else None,
            "model": model,
            "separate_record_key": path,
            "diagnostic_session_id": session_id,
            "expires_at": expires.isoformat(),
        })

    @app.post("/api/v1/diagnostic/<session_id>/submit")
    def diagnostic_submit(session_id: str):
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        answers = payload.get("answers") if isinstance(payload.get("answers"), list) else []
        elapsed = _bounded_int(str(payload.get("elapsed_sec", 0)), 0, 0, 86_400)
        with _connect() as connection:
            session_row = connection.execute(
                "SELECT * FROM diagnostic_sessions WHERE id = ? AND user_id = ?",
                (session_id, str(user["id"])),
            ).fetchone()
            if not session_row:
                return jsonify({"error": "diagnostic_session_not_found"}), 404
            if session_row["submitted_at"]:
                return jsonify({"error": "diagnostic_session_already_submitted"}), 409
            if session_row["expires_at"] < datetime.now(timezone.utc).isoformat():
                return jsonify({"error": "diagnostic_session_expired"}), 409
            question_ids = json.loads(session_row["question_ids_json"] or "[]")
            if not question_ids:
                return jsonify({"error": "empty_diagnostic_session"}), 409
            placeholders = ",".join("?" for _ in question_ids)
            rows = connection.execute(
                f"SELECT id, payload_json FROM questions WHERE id IN ({placeholders})", question_ids
            ).fetchall()
            by_id = {str(row["id"]): json.loads(row["payload_json"]) for row in rows}
            items = [by_id[qid] for qid in question_ids if qid in by_id]
            score = _score_diagnostic_items(
                items, answers,
                path=str(session_row["diagnostic_path"]), model_key=str(session_row["model_key"]),
            )
            cursor = connection.execute(
                """INSERT INTO diagnostic_results
                   (user_id, diagnostic_path, model_key, academic_track, score_percent,
                    group_scores_json, answers_json, elapsed_sec)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(user["id"]), session_row["diagnostic_path"], session_row["model_key"],
                    session_row["academic_track"], score["weighted_percent"],
                    json.dumps(score["groups"], ensure_ascii=False),
                    json.dumps(answers, ensure_ascii=False), elapsed,
                ),
            )
            connection.execute(
                "UPDATE diagnostic_sessions SET submitted_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,)
            )
            connection.commit()
        return jsonify({
            "id": cursor.lastrowid,
            "path": session_row["diagnostic_path"],
            "model": session_row["model_key"],
            "academic_track_used": session_row["academic_track"],
            "score_percent": score["weighted_percent"],
            "raw_percent": score["raw_percent"],
            "correct": score["correct"],
            "total": score["total"],
            "group_scores": score["groups"],
            "separate_record_key": session_row["diagnostic_path"],
        }), 201

    @app.get("/api/v1/summaries")
    def summaries():
        items = list(_summaries())
        for field in ("exam", "subject", "unit"):
            value = (request.args.get(field) or "").strip()
            if value:
                items = [x for x in items if str(x.get(field, "")) == value]
        limit = _bounded_int(request.args.get("limit"), 200, 1, 500)
        result = items[:limit]
        return jsonify({"items": result, "count": len(items), "returned": len(result)})

    @app.post("/api/v1/activity")
    def activity_post():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        activity_type = str(payload.get("type", "learning"))[:40]
        activity_date = str(payload.get("activity_date") or datetime.now(timezone.utc).date().isoformat())
        try:
            date.fromisoformat(activity_date)
        except ValueError:
            return jsonify({"error": "invalid_activity_date"}), 400
        with _connect() as connection:
            connection.execute(
                "INSERT INTO learning_activity (user_id, activity_type, activity_date) VALUES (?, ?, ?)",
                (str(user["id"]), activity_type, activity_date),
            )
            connection.commit()
        return jsonify({"status": "recorded", "streak": _server_streak(str(user["id"]))}), 201

    @app.get("/api/v1/streak")
    def streak_get():
        user, error = _require_user()
        if error:
            return error
        return jsonify(_server_streak(str(user["id"])))

    @app.post("/api/v1/friend-requests")
    def friend_request_create():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        receiver_code = str(payload.get("receiver_code", "")).strip().upper()
        receiver_username = str(payload.get("receiver_username", "")).strip().lower().lstrip("@")
        if not receiver_code and not receiver_username:
            return jsonify({"error": "username_required"}), 400
        sender_id = str(user["id"])
        sender_code = friend_code_for_user(sender_id)
        with _connect() as connection:
            if receiver_username:
                receiver = connection.execute(
                    """SELECT p.user_id, p.friend_code
                       FROM auth_users u
                       JOIN student_profiles p ON p.user_id = CAST(u.id AS TEXT)
                       WHERE u.username = ?""",
                    (receiver_username,),
                ).fetchone()
                if not receiver:
                    return jsonify({"error": "username_not_found"}), 404
                receiver_code = str(receiver["friend_code"] or friend_code_for_user(receiver["user_id"])).upper()
            else:
                if not receiver_code.startswith("SH-") or len(receiver_code) < 7:
                    return jsonify({"error": "invalid_friend_code"}), 400
                receiver = connection.execute(
                    "SELECT user_id, friend_code FROM student_profiles WHERE friend_code = ?", (receiver_code,)
                ).fetchone()
        if receiver_code == sender_code:
            return jsonify({"error": "cannot_add_self"}), 400
        with _connect() as connection:
            receiver = connection.execute(
                "SELECT user_id FROM student_profiles WHERE friend_code = ?", (receiver_code,)
            ).fetchone()
            sender_profile = connection.execute(
                "SELECT user_id FROM student_profiles WHERE user_id = ?", (sender_id,)
            ).fetchone()
            if not sender_profile:
                return jsonify({"error": "profile_required"}), 409
            if not receiver:
                return jsonify({"error": "friend_code_not_found"}), 404
            existing_friend = connection.execute(
                "SELECT 1 FROM friendships WHERE owner_id = ? AND friend_code = ? AND status = 'accepted'",
                (sender_id, receiver_code),
            ).fetchone()
            if existing_friend:
                return jsonify({"error": "already_friends"}), 409
            existing_request = connection.execute(
                "SELECT id FROM friendship_requests WHERE sender_id = ? AND receiver_code = ? AND status = 'pending'",
                (sender_id, receiver_code),
            ).fetchone()
            if existing_request:
                return jsonify({"error": "request_exists", "id": existing_request["id"]}), 409
            cursor = connection.execute(
                "INSERT INTO friendship_requests (sender_id, receiver_code) VALUES (?, ?)",
                (sender_id, receiver_code),
            )
            connection.commit()
        return jsonify({"id": cursor.lastrowid, "status": "pending", "server_time": datetime.now(timezone.utc).isoformat()}), 201

    @app.post("/api/v1/challenges")
    def challenge_create():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        opponent_code = str(payload.get("opponent_code", "")).strip().upper()
        template_id = str(payload.get("template_id", "")).strip()
        templates = {x.get("id"): x for x in load_challenge_templates().get("templates", [])}
        template = templates.get(template_id)
        if not opponent_code.startswith("SH-") or not template:
            return jsonify({"error": "invalid_challenge"}), 400
        owner_id = str(user["id"])
        if opponent_code == friend_code_for_user(owner_id):
            return jsonify({"error": "cannot_challenge_self"}), 400
        count = int(template.get("questions", 10))
        with _connect(query_only=True) as connection:
            friendship = connection.execute(
                "SELECT 1 FROM friendships WHERE owner_id = ? AND friend_code = ? AND status = 'accepted'",
                (owner_id, opponent_code),
            ).fetchone()
            if not friendship:
                return jsonify({"error": "accepted_friendship_required"}), 409
            # The shipped bank is explicitly a development seed. Production deployments
            # must set SUHAIL_ALLOW_DEVELOPMENT_QUESTIONS=0 after approved content exists.
            allow_development = os.environ.get("SUHAIL_ALLOW_DEVELOPMENT_QUESTIONS", "1") == "1"
            if allow_development:
                rows = connection.execute("SELECT id FROM questions ORDER BY RANDOM() LIMIT ?", (count,)).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id FROM questions WHERE json_extract(payload_json, '$.release_eligible') = 1 ORDER BY RANDOM() LIMIT ?",
                    (count,),
                ).fetchall()
        question_ids = [row[0] for row in rows]
        if len(question_ids) < count:
            return jsonify({"error": "insufficient_approved_questions", "required": count, "available": len(question_ids)}), 409
        expiry = datetime.now(timezone.utc) + timedelta(hours=int(load_admin_settings().get("challenges", {}).get("invite_expiry_hours", 48)))
        with _connect() as connection:
            cursor = connection.execute(
                """INSERT INTO challenges
                   (owner_id, opponent_code, template_id, status, question_ids_json, expires_at)
                   VALUES (?, ?, ?, 'pending', ?, ?)""",
                (owner_id, opponent_code, template_id, json.dumps(question_ids), expiry.isoformat()),
            )
            connection.commit()
        return jsonify({"id": cursor.lastrowid, "status": "pending", "question_count": len(question_ids), "expires_at": expiry.isoformat()}), 201


    @app.get("/api/v1/diagnostic-results")
    def diagnostic_results_get():
        user, error = _require_user()
        if error:
            return error
        path = (request.args.get("path") or "").strip().lower()
        if path and path not in {"qudrat", "tahsili"}:
            return jsonify({"error": "invalid_diagnostic_path"}), 400
        sql = "SELECT * FROM diagnostic_results WHERE user_id = ?"
        params: list[Any] = [str(user["id"])]
        if path:
            sql += " AND diagnostic_path = ?"
            params.append(path)
        sql += " ORDER BY created_at DESC LIMIT 50"
        with _connect(query_only=True) as connection:
            rows = connection.execute(sql, params).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["group_scores"] = json.loads(item.pop("group_scores_json") or "{}")
            item.pop("answers_json", None)
            items.append(item)
        latest: dict[str, Any] = {}
        for item in items:
            latest.setdefault(item["diagnostic_path"], item)
        return jsonify({"items": items, "latest": latest, "separate_records": True})

    @app.post("/api/v1/diagnostic-results")
    def diagnostic_results_post():
        if os.environ.get("SUHAIL_ALLOW_CLIENT_SCORED_RESULTS", "0") != "1":
            return jsonify({"error": "use_server_scored_diagnostic_session"}), 410
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        path = str(payload.get("path", "")).strip().lower()
        if path not in {"qudrat", "tahsili"}:
            return jsonify({"error": "path_must_be_qudrat_or_tahsili"}), 400
        academic_track = str(payload.get("academic_track", "scientific")) if path == "qudrat" else None
        if path == "qudrat" and academic_track not in {"scientific", "literary"}:
            return jsonify({"error": "invalid_academic_track"}), 400
        model_key = (
            "qudrat_literary" if path == "qudrat" and academic_track == "literary"
            else "qudrat_scientific" if path == "qudrat"
            else "tahsili_common"
        )
        score = max(0.0, min(100.0, float(payload.get("score_percent", 0))))
        groups = payload.get("group_scores") if isinstance(payload.get("group_scores"), dict) else {}
        answers = payload.get("answers") if isinstance(payload.get("answers"), list) else []
        elapsed = _bounded_int(str(payload.get("elapsed_sec", 0)), 0, 0, 86_400)
        with _connect() as connection:
            cursor = connection.execute(
                """INSERT INTO diagnostic_results
                   (user_id, diagnostic_path, model_key, academic_track, score_percent,
                    group_scores_json, answers_json, elapsed_sec)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(user["id"]), path, model_key, academic_track, score,
                    json.dumps(groups, ensure_ascii=False),
                    json.dumps(answers, ensure_ascii=False), elapsed,
                ),
            )
            connection.commit()
        return jsonify({
            "id": cursor.lastrowid,
            "path": path,
            "model": model_key,
            "academic_track_used": academic_track,
            "score_percent": score,
            "separate_record_key": path,
        }), 201

    @app.get("/api/v1/friend-requests")
    def friend_requests_list():
        user, error = _require_user()
        if error:
            return error
        own_code = friend_code_for_user(str(user["id"]))
        with _connect(query_only=True) as connection:
            incoming = connection.execute(
                """SELECT r.*, p.display_name AS sender_name, p.avatar_id AS sender_avatar,
                          p.friend_code AS sender_code, u.username AS sender_username
                   FROM friendship_requests r
                   LEFT JOIN student_profiles p ON p.user_id = r.sender_id
                   LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = r.sender_id
                   WHERE r.receiver_code = ? ORDER BY r.created_at DESC LIMIT 100""",
                (own_code,),
            ).fetchall()
            outgoing = connection.execute(
                "SELECT * FROM friendship_requests WHERE sender_id = ? ORDER BY created_at DESC LIMIT 100",
                (str(user["id"]),),
            ).fetchall()
        return jsonify({"incoming": [dict(x) for x in incoming], "outgoing": [dict(x) for x in outgoing]})

    @app.post("/api/v1/friend-requests/<int:request_id>/respond")
    def friend_request_respond(request_id: int):
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        action = str(payload.get("action", "")).lower()
        if action not in {"accept", "decline"}:
            return jsonify({"error": "action_must_be_accept_or_decline"}), 400
        own_code = friend_code_for_user(str(user["id"]))
        with _connect() as connection:
            row = connection.execute(
                "SELECT * FROM friendship_requests WHERE id = ? AND receiver_code = ? AND status = 'pending'",
                (request_id, own_code),
            ).fetchone()
            if not row:
                return jsonify({"error": "friend_request_not_found"}), 404
            status = "accepted" if action == "accept" else "declined"
            connection.execute(
                "UPDATE friendship_requests SET status = ?, responded_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, request_id),
            )
            if action == "accept":
                sender = connection.execute(
                    "SELECT * FROM student_profiles WHERE user_id = ?", (row["sender_id"],)
                ).fetchone()
                receiver = connection.execute(
                    "SELECT * FROM student_profiles WHERE user_id = ?", (str(user["id"]),)
                ).fetchone()
                if not sender or not receiver:
                    return jsonify({"error": "both_profiles_required"}), 409
                connection.execute(
                    """INSERT OR IGNORE INTO friendships(owner_id, friend_code, friend_name, avatar_id)
                       VALUES (?, ?, ?, ?)""",
                    (str(user["id"]), sender["friend_code"], sender["display_name"], sender["avatar_id"]),
                )
                connection.execute(
                    """INSERT OR IGNORE INTO friendships(owner_id, friend_code, friend_name, avatar_id)
                       VALUES (?, ?, ?, ?)""",
                    (str(sender["user_id"]), receiver["friend_code"], receiver["display_name"], receiver["avatar_id"]),
                )
            connection.commit()
        return jsonify({"id": request_id, "status": status})

    @app.get("/api/v1/friends")
    def friends_list():
        user, error = _require_user()
        if error:
            return error
        with _connect(query_only=True) as connection:
            rows = connection.execute(
                """SELECT f.friend_code, f.friend_name, f.avatar_id, f.created_at, u.username,
                          CASE WHEN b.blocked_code IS NULL THEN 0 ELSE 1 END AS blocked
                   FROM friendships f
                   LEFT JOIN student_profiles p ON p.friend_code = f.friend_code
                   LEFT JOIN auth_users u ON CAST(u.id AS TEXT) = p.user_id
                   LEFT JOIN user_blocks b ON b.owner_id = f.owner_id AND b.blocked_code = f.friend_code
                   WHERE f.owner_id = ? AND f.status = 'accepted'
                   ORDER BY f.friend_name""",
                (str(user["id"]),),
            ).fetchall()
        return jsonify({"items": [dict(row) for row in rows]})

    @app.get("/api/v1/challenges")
    def challenges_list():
        user, error = _require_user()
        if error:
            return error
        own_code = friend_code_for_user(str(user["id"]))
        with _connect(query_only=True) as connection:
            rows = connection.execute(
                """SELECT id, owner_id, opponent_code, template_id, status,
                          owner_score, owner_elapsed_sec, opponent_score, opponent_elapsed_sec,
                          created_at, accepted_at, completed_at, expires_at
                   FROM challenges WHERE owner_id = ? OR opponent_code = ?
                   ORDER BY created_at DESC LIMIT 100""",
                (str(user["id"]), own_code),
            ).fetchall()
        return jsonify({"items": [dict(row) for row in rows], "friend_code": own_code})

    @app.get("/api/v1/challenges/<int:challenge_id>")
    def challenge_detail(challenge_id: int):
        user, error = _require_user()
        if error:
            return error
        own_code = friend_code_for_user(str(user["id"]))
        with _connect(query_only=True) as connection:
            challenge = connection.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
            if not challenge:
                return jsonify({"error": "challenge_not_found"}), 404
            if str(challenge["owner_id"]) != str(user["id"]) and str(challenge["opponent_code"]) != own_code:
                return jsonify({"error": "challenge_access_denied"}), 403
            question_ids = json.loads(challenge["question_ids_json"] or "[]")
            items: list[dict[str, Any]] = []
            if challenge["status"] in {"active", "completed"} and question_ids:
                placeholders = ",".join("?" for _ in question_ids)
                rows = connection.execute(
                    f"SELECT id, payload_json FROM questions WHERE id IN ({placeholders})", question_ids
                ).fetchall()
                by_id = {str(row["id"]): json.loads(row["payload_json"]) for row in rows}
                items = [_public_question(by_id[qid]) for qid in question_ids if qid in by_id]
        payload = dict(challenge)
        payload.pop("question_ids_json", None)
        payload["items"] = items
        payload["question_count"] = len(question_ids)
        return jsonify(payload)

    @app.post("/api/v1/challenges/<int:challenge_id>/accept")
    def challenge_accept(challenge_id: int):
        user, error = _require_user()
        if error:
            return error
        own_code = friend_code_for_user(str(user["id"]))
        with _connect() as connection:
            row = connection.execute(
                "SELECT * FROM challenges WHERE id = ? AND opponent_code = ? AND status = 'pending'",
                (challenge_id, own_code),
            ).fetchone()
            if not row:
                return jsonify({"error": "challenge_not_found"}), 404
            if row["expires_at"] and row["expires_at"] < datetime.now(timezone.utc).isoformat():
                connection.execute("UPDATE challenges SET status = 'expired' WHERE id = ?", (challenge_id,))
                connection.commit()
                return jsonify({"error": "challenge_expired"}), 409
            connection.execute(
                "UPDATE challenges SET status = 'active', accepted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (challenge_id,),
            )
            connection.commit()
        return jsonify({"id": challenge_id, "status": "active"})

    @app.post("/api/v1/challenges/<int:challenge_id>/submit")
    def challenge_submit(challenge_id: int):
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        answers = payload.get("answers") if isinstance(payload.get("answers"), list) else []
        elapsed_sec = _bounded_int(str(payload.get("elapsed_sec", 0)), 0, 0, 86_400)
        own_code = friend_code_for_user(str(user["id"]))
        with _connect() as connection:
            challenge = connection.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
            if not challenge or str(challenge["status"]) not in {"active", "pending"}:
                return jsonify({"error": "challenge_not_active"}), 409
            is_owner = str(challenge["owner_id"]) == str(user["id"])
            is_opponent = str(challenge["opponent_code"]) == own_code
            if not (is_owner or is_opponent):
                return jsonify({"error": "challenge_access_denied"}), 403
            allowed_ids = set(json.loads(challenge["question_ids_json"] or "[]"))
            score = 0
            for answer in answers:
                qid = str(answer.get("question_id", ""))
                if qid not in allowed_ids:
                    continue
                qrow = connection.execute("SELECT payload_json FROM questions WHERE id = ?", (qid,)).fetchone()
                if not qrow:
                    continue
                question = json.loads(qrow[0])
                selected = answer.get("selected_index")
                correct = int(selected == question.get("correct"))
                score += correct
                connection.execute(
                    """INSERT OR REPLACE INTO challenge_answers
                       (challenge_id, user_id, question_id, selected_index, is_correct, elapsed_ms)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (challenge_id, str(user["id"]), qid, selected, correct, int(answer.get("elapsed_ms", 0) or 0)),
                )
            if is_owner:
                connection.execute(
                    "UPDATE challenges SET owner_score = ?, owner_elapsed_sec = ? WHERE id = ?",
                    (score, elapsed_sec, challenge_id),
                )
            else:
                connection.execute(
                    "UPDATE challenges SET opponent_score = ?, opponent_elapsed_sec = ? WHERE id = ?",
                    (score, elapsed_sec, challenge_id),
                )
            current = connection.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
            completed = current["owner_score"] is not None and current["opponent_score"] is not None
            if completed:
                connection.execute(
                    "UPDATE challenges SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (challenge_id,),
                )
            connection.commit()
        scoreboard = {
            "owner_score": current["owner_score"],
            "owner_elapsed_sec": current["owner_elapsed_sec"],
            "opponent_score": current["opponent_score"],
            "opponent_elapsed_sec": current["opponent_elapsed_sec"],
        }
        winner = None
        if completed:
            owner_tuple = (int(current["owner_score"] or 0), -int(current["owner_elapsed_sec"] or 0))
            opponent_tuple = (int(current["opponent_score"] or 0), -int(current["opponent_elapsed_sec"] or 0))
            winner = "owner" if owner_tuple > opponent_tuple else "opponent" if opponent_tuple > owner_tuple else "tie"
        return jsonify({
            "id": challenge_id,
            "score": score,
            "answered": len(answers),
            "status": "completed" if completed else "waiting",
            "winner": winner,
            "scoreboard": scoreboard,
        })

    @app.post("/api/v1/blocks")
    def block_user():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        blocked_code = str(payload.get("friend_code", "")).strip().upper()
        if not blocked_code.startswith("SH-"):
            return jsonify({"error": "invalid_friend_code"}), 400
        own_id = str(user["id"])
        if blocked_code == friend_code_for_user(own_id):
            return jsonify({"error": "cannot_block_self"}), 400
        with _connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO user_blocks(owner_id, blocked_code) VALUES (?, ?)",
                (own_id, blocked_code),
            )
            connection.commit()
        return jsonify({"status": "blocked", "friend_code": blocked_code}), 201

    @app.post("/api/v1/reports")
    def report_user():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        reported_code = str(payload.get("friend_code", "")).strip().upper()
        reason = str(payload.get("reason", "اسم أو يوزر غير مناسب")).strip()[:300]
        if not reported_code.startswith("SH-") or not reason:
            return jsonify({"error": "invalid_report"}), 400
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO user_reports(reporter_id, reported_code, reason) VALUES (?, ?, ?)",
                (str(user["id"]), reported_code, reason),
            )
            connection.commit()
        return jsonify({"id": cursor.lastrowid, "status": "received"}), 201

    @app.post("/api/v1/group-challenges")
    def group_challenge_create():
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        exam = str(payload.get("exam", "")).strip()
        if exam not in ALLOWED_EXAMS:
            return jsonify({"error": "invalid_exam"}), 400
        try:
            requested_count = int(payload.get("question_count", 10))
        except (TypeError, ValueError):
            requested_count = 10
        question_count = requested_count if requested_count in {5, 10, 15, 20} else 10
        friend_codes = []
        for raw in payload.get("friend_codes", []) if isinstance(payload.get("friend_codes"), list) else []:
            code = str(raw).strip().upper()
            if code and code not in friend_codes:
                friend_codes.append(code)
        if not friend_codes:
            return jsonify({"error": "at_least_one_friend_required"}), 400
        if len(friend_codes) > 9:
            return jsonify({"error": "participant_limit", "maximum_players": 10}), 400
        owner_id = str(user["id"])
        room_id = "SHG-" + uuid.uuid4().hex[:10].upper()
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        with _connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            owner_profile = _ensure_profile_for_user(connection, user)
            members: list[sqlite3.Row] = []
            for code in friend_codes:
                if code == owner_profile["friend_code"]:
                    return jsonify({"error": "cannot_invite_self"}), 400
                friendship = connection.execute(
                    "SELECT 1 FROM friendships WHERE owner_id = ? AND friend_code = ? AND status='accepted'",
                    (owner_id, code),
                ).fetchone()
                blocked = connection.execute(
                    "SELECT 1 FROM user_blocks WHERE (owner_id = ? AND blocked_code = ?) OR (owner_id = (SELECT user_id FROM student_profiles WHERE friend_code = ?) AND blocked_code = ?)",
                    (owner_id, code, code, owner_profile["friend_code"]),
                ).fetchone()
                member = _group_member_profile(connection, code)
                if not friendship or not member or blocked:
                    connection.rollback()
                    return jsonify({"error": "accepted_friendship_required", "friend_code": code}), 409
                members.append(member)
            allow_development = os.environ.get("SUHAIL_ALLOW_DEVELOPMENT_QUESTIONS", "1") == "1"
            if allow_development:
                rows = connection.execute(
                    "SELECT id FROM questions WHERE exam = ? ORDER BY RANDOM() LIMIT ?",
                    (exam, question_count),
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT id FROM questions WHERE exam = ?
                       AND json_extract(payload_json, '$.release_eligible') = 1
                       ORDER BY RANDOM() LIMIT ?""",
                    (exam, question_count),
                ).fetchall()
            question_ids = [str(row[0]) for row in rows]
            if len(question_ids) < question_count:
                connection.rollback()
                return jsonify({"error": "insufficient_approved_questions", "required": question_count, "available": len(question_ids)}), 409
            connection.execute(
                """INSERT INTO group_challenges
                   (id, owner_id, exam, question_count, question_time_sec, question_ids_json, status, expires_at)
                   VALUES (?, ?, ?, ?, 30, ?, 'pending', ?)""",
                (room_id, owner_id, exam, question_count, json.dumps(question_ids), expiry.isoformat()),
            )
            connection.execute(
                """INSERT INTO group_challenge_members
                   (room_id, user_id, friend_code, display_name, username, status, joined_at, last_seen_at)
                   VALUES (?, ?, ?, ?, ?, 'owner', ?, ?)""",
                (
                    room_id,
                    owner_id,
                    owner_profile["friend_code"],
                    owner_profile["display_name"],
                    owner_profile["username"],
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            for member in members:
                connection.execute(
                    """INSERT INTO group_challenge_members
                       (room_id, user_id, friend_code, display_name, username, status)
                       VALUES (?, ?, ?, ?, ?, 'invited')""",
                    (room_id, str(member["user_id"]), member["friend_code"], member["display_name"], member["username"]),
                )
            connection.commit()
        return jsonify({
            "id": room_id,
            "status": "pending",
            "maximum_players": 10,
            "invited": len(members),
            "question_count": question_count,
            "question_time_sec": 30,
            "expires_at": expiry.isoformat(),
        }), 201

    @app.get("/api/v1/group-challenges")
    def group_challenges_list():
        user, error = _require_user()
        if error:
            return error
        user_id = str(user["id"])
        with _connect() as connection:
            rows = connection.execute(
                """SELECT g.id, g.exam, g.status, g.question_count, g.question_time_sec,
                          g.current_index, g.owner_id, g.created_at, g.started_at, g.completed_at,
                          m.status AS my_status,
                          (SELECT COUNT(*) FROM group_challenge_members x WHERE x.room_id=g.id AND x.status IN ('owner','accepted')) AS accepted_players,
                          (SELECT COUNT(*) FROM group_challenge_members x WHERE x.room_id=g.id) AS total_invited
                   FROM group_challenges g
                   JOIN group_challenge_members m ON m.room_id=g.id AND m.user_id=?
                   ORDER BY g.created_at DESC LIMIT 100""",
                (user_id,),
            ).fetchall()
        return jsonify({"items": [dict(row) for row in rows], "maximum_players": 10, "question_time_sec": 30})

    @app.post("/api/v1/group-challenges/<room_id>/respond")
    def group_challenge_respond(room_id: str):
        user, error = _require_user()
        if error:
            return error
        action = str((request.get_json(silent=True) or {}).get("action", "")).strip().lower()
        if action not in {"accept", "decline"}:
            return jsonify({"error": "invalid_action"}), 400
        user_id = str(user["id"])
        with _connect() as connection:
            row = connection.execute(
                "SELECT status FROM group_challenge_members WHERE room_id=? AND user_id=?",
                (room_id, user_id),
            ).fetchone()
            room = connection.execute("SELECT * FROM group_challenges WHERE id=?", (room_id,)).fetchone()
            if not row or not room:
                return jsonify({"error": "group_challenge_not_found"}), 404
            if row["status"] != "invited" or room["status"] != "pending":
                return jsonify({"error": "invite_not_pending"}), 409
            status = "accepted" if action == "accept" else "declined"
            connection.execute(
                "UPDATE group_challenge_members SET status=?, joined_at=?, last_seen_at=? WHERE room_id=? AND user_id=?",
                (status, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), room_id, user_id),
            )
            connection.commit()
        return jsonify({"id": room_id, "status": status})

    @app.post("/api/v1/group-challenges/<room_id>/start")
    def group_challenge_start(room_id: str):
        user, error = _require_user()
        if error:
            return error
        user_id = str(user["id"])
        with _connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            room = connection.execute("SELECT * FROM group_challenges WHERE id=?", (room_id,)).fetchone()
            if not room:
                connection.rollback()
                return jsonify({"error": "group_challenge_not_found"}), 404
            if str(room["owner_id"]) != user_id:
                connection.rollback()
                return jsonify({"error": "owner_required"}), 403
            if room["status"] != "pending":
                connection.rollback()
                return jsonify({"error": "group_challenge_not_pending"}), 409
            accepted = connection.execute(
                "SELECT COUNT(*) FROM group_challenge_members WHERE room_id=? AND status IN ('owner','accepted')",
                (room_id,),
            ).fetchone()[0]
            if int(accepted) < 2:
                connection.rollback()
                return jsonify({"error": "at_least_two_players_required"}), 409
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                """UPDATE group_challenges SET status='active', current_index=0,
                   question_started_at=?, started_at=?, last_event='started' WHERE id=?""",
                (now, now, room_id),
            )
            connection.commit()
        return jsonify({"id": room_id, "status": "active", "question_time_sec": 30})

    @app.get("/api/v1/group-challenges/<room_id>/state")
    def group_challenge_state(room_id: str):
        user, error = _require_user()
        if error:
            return error
        user_id = str(user["id"])
        try:
            with _connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                room = _advance_group_if_expired(connection, room_id)
                if not room:
                    connection.rollback()
                    return jsonify({"error": "group_challenge_not_found"}), 404
                connection.execute(
                    "UPDATE group_challenge_members SET last_seen_at=? WHERE room_id=? AND user_id=?",
                    (datetime.now(timezone.utc).isoformat(), room_id, user_id),
                )
                payload = _group_state_payload(connection, room, user_id)
                connection.commit()
            return jsonify(payload)
        except PermissionError:
            return jsonify({"error": "group_challenge_access_denied"}), 403

    @app.post("/api/v1/group-challenges/<room_id>/answer")
    def group_challenge_answer(room_id: str):
        user, error = _require_user()
        if error:
            return error
        payload = request.get_json(silent=True) or {}
        try:
            selected_index = int(payload.get("selected_index"))
            expected_index = int(payload.get("question_index"))
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_answer"}), 400
        user_id = str(user["id"])
        with _connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            room = _advance_group_if_expired(connection, room_id)
            member = connection.execute(
                "SELECT * FROM group_challenge_members WHERE room_id=? AND user_id=? AND status IN ('owner','accepted')",
                (room_id, user_id),
            ).fetchone()
            if not room or not member:
                connection.rollback()
                return jsonify({"error": "group_challenge_access_denied"}), 403
            if room["status"] != "active":
                state = _group_state_payload(connection, room, user_id)
                connection.commit()
                return jsonify({"error": "group_challenge_not_active", "state": state}), 409
            current_index = int(room["current_index"] or 0)
            if current_index != expected_index:
                state = _group_state_payload(connection, room, user_id)
                connection.commit()
                return jsonify({"error": "question_advanced", "state": state}), 409
            duplicate = connection.execute(
                "SELECT 1 FROM group_challenge_answers WHERE room_id=? AND question_index=? AND user_id=?",
                (room_id, current_index, user_id),
            ).fetchone()
            if duplicate:
                state = _group_state_payload(connection, room, user_id)
                connection.commit()
                return jsonify({"error": "already_answered", "state": state}), 409
            question_ids = json.loads(room["question_ids_json"] or "[]")
            if current_index >= len(question_ids):
                connection.rollback()
                return jsonify({"error": "question_not_found"}), 404
            question_id = str(question_ids[current_index])
            qrow = connection.execute("SELECT payload_json FROM questions WHERE id=?", (question_id,)).fetchone()
            if not qrow:
                connection.rollback()
                return jsonify({"error": "question_not_found"}), 404
            question = json.loads(qrow[0])
            is_correct = int(selected_index == int(question.get("correct", -1)))
            started = _parse_utc(room["question_started_at"])
            elapsed_ms = max(0, min(30_000, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))) if started else 30_000
            connection.execute(
                """INSERT INTO group_challenge_answers
                   (room_id, question_index, question_id, user_id, selected_index, is_correct, elapsed_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (room_id, current_index, question_id, user_id, selected_index, is_correct, elapsed_ms),
            )
            won = False
            if is_correct:
                won = True
                connection.execute(
                    """UPDATE group_challenge_members SET score=score+1, correct_count=correct_count+1,
                       total_response_ms=total_response_ms+? WHERE room_id=? AND user_id=?""",
                    (elapsed_ms, room_id, user_id),
                )
                next_index = current_index + 1
                now = datetime.now(timezone.utc).isoformat()
                if next_index >= int(room["question_count"]):
                    connection.execute(
                        """UPDATE group_challenges SET status='completed', current_index=?, completed_at=?,
                           last_event='correct', last_winner_user_id=?, last_winner_name=?, last_winner_elapsed_ms=?
                           WHERE id=?""",
                        (next_index, now, user_id, member["display_name"], elapsed_ms, room_id),
                    )
                else:
                    connection.execute(
                        """UPDATE group_challenges SET current_index=?, question_started_at=?,
                           last_event='correct', last_winner_user_id=?, last_winner_name=?, last_winner_elapsed_ms=?
                           WHERE id=?""",
                        (next_index, now, user_id, member["display_name"], elapsed_ms, room_id),
                    )
            room = connection.execute("SELECT * FROM group_challenges WHERE id=?", (room_id,)).fetchone()
            state = _group_state_payload(connection, room, user_id)
            connection.commit()
        return jsonify({"correct": bool(is_correct), "won_point": won, "elapsed_ms": elapsed_ms, "state": state})

    @app.delete("/api/v1/account")
    def account_delete():
        user, error = _require_user()
        if error:
            return error
        user_id = str(user["id"])
        own_code = friend_code_for_user(user_id)
        with _connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            owned_room_ids = [row[0] for row in connection.execute(
                "SELECT id FROM group_challenges WHERE owner_id=?", (user_id,)
            ).fetchall()]
            for room_id in owned_room_ids:
                connection.execute("DELETE FROM group_challenge_answers WHERE room_id=?", (room_id,))
                connection.execute("DELETE FROM group_challenge_members WHERE room_id=?", (room_id,))
                connection.execute("DELETE FROM group_challenges WHERE id=?", (room_id,))
            member_room_ids = [row[0] for row in connection.execute(
                "SELECT room_id FROM group_challenge_members WHERE user_id=?", (user_id,)
            ).fetchall()]
            for room_id in member_room_ids:
                connection.execute("DELETE FROM group_challenge_answers WHERE room_id=? AND user_id=?", (room_id, user_id))
                connection.execute("DELETE FROM group_challenge_members WHERE room_id=? AND user_id=?", (room_id, user_id))
            connection.execute("DELETE FROM friendship_requests WHERE sender_id=? OR receiver_code=?", (user_id, own_code))
            connection.execute("DELETE FROM friendships WHERE owner_id=? OR friend_code=?", (user_id, own_code))
            connection.execute("DELETE FROM challenges WHERE owner_id=? OR opponent_code=?", (user_id, own_code))
            connection.execute("DELETE FROM challenge_answers WHERE user_id=?", (user_id,))
            connection.execute("DELETE FROM diagnostic_sessions WHERE user_id=?", (user_id,))
            connection.execute("DELETE FROM diagnostic_results WHERE user_id=?", (user_id,))
            connection.execute("DELETE FROM learning_activity WHERE user_id=?", (user_id,))
            connection.execute("DELETE FROM user_blocks WHERE owner_id=? OR blocked_code=?", (user_id, own_code))
            connection.execute("DELETE FROM user_reports WHERE reporter_id=? OR reported_code=?", (user_id, own_code))
            connection.execute("DELETE FROM student_profiles WHERE user_id=?", (user_id,))
            connection.execute("DELETE FROM auth_tokens WHERE user_id=?", (int(user["id"]),))
            connection.execute("DELETE FROM auth_users WHERE id=?", (int(user["id"]),))
            connection.commit()
        return jsonify({"status": "deleted"})

    @app.get("/api/v1/admin/settings")
    def admin_settings_get():
        if not _admin_authorized():
            return jsonify({"error": "admin_token_required"}), 401
        return jsonify(load_admin_settings())

    @app.put("/api/v1/admin/settings")
    def admin_settings_put():
        if not _admin_authorized():
            return jsonify({"error": "admin_token_required"}), 401
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("general"), dict):
            return jsonify({"error": "invalid_settings_payload"}), 400
        diagnostic_cfg = payload.get("diagnostic", {})
        if "tahsili_common" not in diagnostic_cfg or "qudrat_scientific" not in diagnostic_cfg or "qudrat_literary" not in diagnostic_cfg:
            return jsonify({"error": "diagnostic_configuration_must_remain_separate"}), 400
        ADMIN_SETTINGS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        invalidate_config_cache()
        return jsonify({"status": "saved", "release": RELEASE})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "not_found"}), 404

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Suhail-Release"] = RELEASE
        public_cache_paths = {
            "/health", "/api/v1/config/public", "/api/v1/avatars",
            "/api/v1/challenges/templates", "/api/v1/scoring/models", "/api/v1/catalog",
        }
        is_public_cache = request.path in public_cache_paths or request.path == "/api/v1/summaries"
        if request.method == "GET" and response.status_code == 200 and is_public_cache:
            response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
        else:
            # Never allow shared caches to retain profiles, tokens, activity, diagnostics or social data.
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["Pragma"] = "no-cache"
        accepts_gzip = "gzip" in request.headers.get("Accept-Encoding", "").lower()
        if accepts_gzip and response.mimetype == "application/json" and len(response.get_data()) > 1024:
            response.set_data(gzip.compress(response.get_data(), compresslevel=5))
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(response.get_data()))
            response.headers["Vary"] = "Accept-Encoding"
        return response

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
