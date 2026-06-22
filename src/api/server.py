from __future__ import annotations

import gzip
import json
import os
import secrets
import sqlite3
import time
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
RELEASE = "62.0.0"
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
                ("كيمياء", "chemistry_weight"), ("أحياء", "biology_weight"),
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
    allowed_origins = [x.strip() for x in os.environ.get("SUHAIL_ALLOWED_ORIGINS", "http://127.0.0.1:8501,http://localhost:8501").split(",") if x.strip()]
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
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "email_exists"}), 409
        except ValueError:
            return jsonify({"error": "invalid_credentials"}), 400
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
            row = connection.execute("SELECT * FROM student_profiles WHERE user_id = ?", (str(user["id"]),)).fetchone()
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
            for subject, key in (("رياضيات", "math"), ("فيزياء", "physics"), ("كيمياء", "chemistry"), ("أحياء", "biology")):
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
        limit = _bounded_int(request.args.get("limit"), 100, 1, 500)
        result = items[:limit]
        return jsonify({"items": result, "count": len(result)})

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
        if not receiver_code.startswith("SH-") or len(receiver_code) < 7:
            return jsonify({"error": "invalid_friend_code"}), 400
        sender_id = str(user["id"])
        sender_code = friend_code_for_user(sender_id)
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
                          p.friend_code AS sender_code
                   FROM friendship_requests r
                   LEFT JOIN student_profiles p ON p.user_id = r.sender_id
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
                "SELECT friend_code, friend_name, avatar_id, created_at FROM friendships WHERE owner_id = ? AND status = 'accepted' ORDER BY friend_name",
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
