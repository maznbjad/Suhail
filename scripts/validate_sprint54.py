from __future__ import annotations

import json
import os
import py_compile
import shutil
import sqlite3
import subprocess
import tempfile
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / "docs" / "reports" / "SPRINT_54_CHECKS.json"
checks: dict[str, object] = {"release": "54.0.0", "checks": {}}


def ok(name: str, detail: object = True) -> None:
    checks["checks"][name] = {"ok": True, "detail": detail}


def fail(name: str, detail: object) -> None:
    checks["checks"][name] = {"ok": False, "detail": detail}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(f"{name}: {detail}")


required = [
    "app.py",
    "src/ui/sprint54.css",
    "src/ui/sprint54_experience.js",
    "src/api/server.py",
    "src/core/auth_repository.py",
    "src/core/challenge_repository.py",
    "data/admin/admin_settings.json",
    "data/scoring/score_models.json",
    "data/questions.json",
    "data/suhail_learning.db",
    "docs/reports/SPRINT_50_QUESTION_AUDIT.json",
]
missing = [name for name in required if not (ROOT / name).exists()]
if missing:
    fail("required_files", missing)
ok("required_files", len(required))

settings = json.loads((ROOT / "data/admin/admin_settings.json").read_text(encoding="utf-8"))
diagnostic = settings.get("diagnostic", {})
required_diagnostic = {"qudrat_scientific", "qudrat_literary", "tahsili_common"}
if not required_diagnostic.issubset(diagnostic):
    fail("diagnostic_config", sorted(diagnostic))
if any(key.startswith("tahsili_") and key not in {"tahsili_common", "tahsili_ignores_academic_track"} for key in diagnostic):
    fail("tahsili_common_only", sorted(diagnostic))
if not diagnostic.get("separate_records") or not diagnostic.get("allow_both_exam_goals"):
    fail("diagnostic_independence", diagnostic)
if not diagnostic.get("qudrat_requires_academic_track") or not diagnostic.get("tahsili_ignores_academic_track"):
    fail("track_scope", diagnostic)
ok("diagnostic_config", {
    "qudrat_scientific": diagnostic["qudrat_scientific"],
    "qudrat_literary": diagnostic["qudrat_literary"],
    "tahsili_common": diagnostic["tahsili_common"],
})

models = json.loads((ROOT / "data/scoring/score_models.json").read_text(encoding="utf-8"))
model_keys = set(models.get("models", {}))
if model_keys != required_diagnostic:
    fail("score_models_separate", sorted(model_keys))
ok("score_models_separate", sorted(model_keys))

questions = json.loads((ROOT / "data/questions.json").read_text(encoding="utf-8"))
if len(questions) != 1000:
    fail("question_count", len(questions))
ids = [str(item.get("id", "")) for item in questions]
if len(set(ids)) != len(ids) or "" in ids:
    fail("question_ids", "duplicate_or_blank")
exam_counts = Counter(item.get("exam") for item in questions)
if exam_counts != {"قدرات كمي": 300, "قدرات لفظي": 300, "تحصيلي": 400}:
    fail("question_distribution", dict(exam_counts))
release_eligible = sum(bool(item.get("release_eligible")) for item in questions)
if release_eligible != 0:
    fail("development_bank_guard", release_eligible)
for item in questions:
    choices = item.get("choices")
    correct = item.get("correct")
    if not isinstance(choices, list) or len(choices) != 4 or not isinstance(correct, int) or not 0 <= correct < 4:
        fail("question_shape", item.get("id"))
    if str(item.get("answer")) != str(choices[correct]):
        fail("question_answer_alignment", item.get("id"))
ok("question_bank", {"count": len(questions), "distribution": dict(exam_counts), "release_eligible": 0})

audit = json.loads((ROOT / "docs/reports/SPRINT_50_QUESTION_AUDIT.json").read_text(encoding="utf-8"))
if int(audit.get("repairs_applied_total", 0)) < 18 or int(audit.get("errors_after_repair", 1)) != 0:
    fail("question_audit", audit)
ok("question_audit", {"repairs": audit.get("repairs_applied_total"), "errors_after": audit.get("errors_after_repair")})

users = json.loads((ROOT / "data/users.json").read_text(encoding="utf-8"))
if users not in ([], {}):
    fail("plaintext_users_removed", "data/users.json is not empty")
ok("plaintext_users_removed")

with sqlite3.connect(ROOT / "data/suhail_learning.db") as connection:
    db_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if db_count != 1000:
    fail("sqlite_question_count", db_count)
needed_tables = {"auth_users", "auth_tokens", "student_profiles", "diagnostic_sessions", "diagnostic_results", "friendship_requests", "friendships", "challenges", "challenge_answers", "learning_activity"}
if not needed_tables.issubset(tables):
    fail("sqlite_sprint54_tables", sorted(needed_tables - tables))
ok("sqlite_schema", {"questions": db_count, "tables": sorted(needed_tables)})

python_files = [
    ROOT / "app.py",
    ROOT / "src/api/server.py",
    ROOT / "src/core/auth_repository.py",
    ROOT / "src/core/challenge_repository.py",
    ROOT / "src/core/student_scoring.py",
]
for source in python_files:
    py_compile.compile(str(source), doraise=True)
subprocess.run(["node", "--check", str(ROOT / "src/ui/sprint54_experience.js")], check=True, capture_output=True, text=True)
ok("syntax", {"python": len(python_files), "javascript": 1})

app_source = (ROOT / "app.py").read_text(encoding="utf-8")
for marker in ("sprint54.css", "sprint54_experience.js", "__S54_ADMIN_SETTINGS__", "__S54_SCORE_MODELS__"):
    if marker not in app_source:
        fail("app_injection", marker)
js_source = (ROOT / "src/ui/sprint54_experience.js").read_text(encoding="utf-8")
for marker in (
    "examGoals:['qudrat','tahsili']",
    "tahsili_common",
    "قياسان منفصلان",
    "s54-bottom-nav",
    "s54-mode-summary",
    "s54-mode-exam",
    "svg('fire')",
    "svg('hourglass')",
):
    if marker not in js_source:
        fail("ui_contract", marker)
ok("ui_contract", "final navigation, SVG streak, independent diagnostics")

# API integration is exercised against a temporary copy so validation never pollutes the shipped database.
with tempfile.TemporaryDirectory(prefix="suhail54_") as temp_dir:
    temp_db = Path(temp_dir) / "test.db"
    shutil.copy2(ROOT / "data/suhail_learning.db", temp_db)
    import src.api.server as server

    server.DB_PATH = temp_db
    server._AUTH_ATTEMPTS.clear()
    test_app = server.create_app()
    client = test_app.test_client()

    health = client.get("/health")
    if health.status_code != 200 or health.json.get("release") != "54.0.0":
        fail("api_health", health.get_json())

    def register(email: str, name: str) -> tuple[str, dict]:
        response = client.post("/api/v1/auth/register", json={"email": email, "password": "TestPass54!", "display_name": name})
        if response.status_code != 201:
            fail("api_register", response.get_json())
        return response.json["token"], response.json["user"]

    token_a, user_a = register("student.a@suhail.test", "طالب أ")
    token_b, user_b = register("student.b@suhail.test", "طالب ب")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    profile_a = client.put("/api/v1/profile", headers=headers_a, json={
        "display_name": "طالب أ", "academic_track": "literary", "exam_goals": ["qudrat", "tahsili"], "avatar_id": "male_01"
    })
    profile_b = client.put("/api/v1/profile", headers=headers_b, json={
        "display_name": "طالب ب", "academic_track": "scientific", "exam_goals": ["qudrat", "tahsili"], "avatar_id": "female_01"
    })
    if profile_a.status_code != 200 or profile_b.status_code != 200:
        fail("api_profiles", {"a": profile_a.get_json(), "b": profile_b.get_json()})
    if set(profile_a.json["profile"]["exam_goals"]) != {"qudrat", "tahsili"}:
        fail("api_both_goals", profile_a.json)

    question_page = client.get("/api/v1/questions?limit=5", headers=headers_a)
    if question_page.status_code != 200 or question_page.json.get("count") != 5:
        fail("api_question_page", question_page.get_json())
    if any("correct" in item or "answer" in item for item in question_page.json.get("items", [])):
        fail("api_question_answer_leak", question_page.get_json())
    grade_payload = {
        "answers": [{"question_id": item["id"], "selected_index": 0} for item in question_page.json["items"]]
    }
    grade = client.post("/api/v1/questions/grade", headers=headers_a, json=grade_payload)
    if grade.status_code != 200 or grade.json.get("total") != 5:
        fail("api_server_practice_grading", grade.get_json())
    ok("api_question_security", {"page_size": 5, "answers_hidden": True, "server_grading": True})

    mixed = client.get("/api/v1/diagnostic?path=all", headers=headers_a)
    q_sc = client.get("/api/v1/diagnostic?path=qudrat&track=scientific", headers=headers_a)
    q_li = client.get("/api/v1/diagnostic?path=qudrat&track=literary", headers=headers_a)
    t_sc = client.get("/api/v1/diagnostic?path=tahsili&track=scientific", headers=headers_a)
    t_li = client.get("/api/v1/diagnostic?path=tahsili&track=literary", headers=headers_a)
    if mixed.status_code != 400:
        fail("api_reject_mixed_diagnostic", mixed.status_code)
    if q_sc.json.get("model") != "qudrat_scientific" or q_li.json.get("model") != "qudrat_literary":
        fail("api_qudrat_track_models", {"scientific": q_sc.json, "literary": q_li.json})
    if t_sc.json.get("model") != "tahsili_common" or t_li.json.get("model") != "tahsili_common":
        fail("api_tahsili_common", {"scientific": t_sc.json, "literary": t_li.json})
    if t_sc.json.get("track_used") is not None or t_li.json.get("track_used") is not None:
        fail("api_tahsili_ignores_track", {"scientific": t_sc.json, "literary": t_li.json})
    if [item.get("id") for item in t_sc.json.get("items", [])] != [item.get("id") for item in t_li.json.get("items", [])]:
        fail("api_tahsili_same_questions", "track changed the Tahsili diagnostic")
    leaked = [
        item.get("id") for response in (q_sc, q_li, t_sc, t_li)
        for item in response.json.get("items", [])
        if "correct" in item or "answer" in item
    ]
    if leaked:
        fail("api_diagnostic_answer_leak", leaked[:5])

    def submit_session(response):
        answers = [{"question_id": item["id"], "selected_index": 0} for item in response.json.get("items", [])]
        return client.post(
            f"/api/v1/diagnostic/{response.json['diagnostic_session_id']}/submit",
            headers=headers_a,
            json={"answers": answers, "elapsed_sec": 300},
        )

    result_q = submit_session(q_li)
    result_t = submit_session(t_li)
    if result_q.status_code != 201 or result_t.status_code != 201:
        fail("api_server_scored_diagnostic", {"q": result_q.get_json(), "t": result_t.get_json()})
    latest = client.get("/api/v1/diagnostic-results", headers=headers_a)
    if result_q.json.get("model") != "qudrat_literary" or result_t.json.get("model") != "tahsili_common":
        fail("api_diagnostic_result_models", {"q": result_q.json, "t": result_t.json})
    if result_t.json.get("academic_track_used") is not None or set(latest.json.get("latest", {})) != {"qudrat", "tahsili"}:
        fail("api_independent_result_records", latest.get_json())
    legacy = client.post("/api/v1/diagnostic-results", headers=headers_a, json={"path": "tahsili", "score_percent": 100})
    if legacy.status_code != 410:
        fail("api_reject_client_scored_result", legacy.status_code)
    ok("api_diagnostics", {
        "mixed_rejected": True,
        "answers_hidden": True,
        "server_scored_sessions": True,
        "qudrat_scientific": q_sc.json.get("count"),
        "qudrat_literary": q_li.json.get("count"),
        "tahsili_common": t_sc.json.get("count"),
    })

    code_b = profile_b.json["profile"]["friend_code"]
    friend_request = client.post("/api/v1/friend-requests", headers=headers_a, json={"receiver_code": code_b})
    if friend_request.status_code != 201:
        fail("api_friend_request", friend_request.get_json())
    response = client.post(f"/api/v1/friend-requests/{friend_request.json['id']}/respond", headers=headers_b, json={"action": "accept"})
    if response.status_code != 200 or response.json.get("status") != "accepted":
        fail("api_friend_accept", response.get_json())
    friends_a = client.get("/api/v1/friends", headers=headers_a)
    if len(friends_a.json.get("items", [])) != 1:
        fail("api_friendship", friends_a.get_json())

    challenge = client.post("/api/v1/challenges", headers=headers_a, json={"opponent_code": code_b, "template_id": "speed_5"})
    if challenge.status_code != 201:
        fail("api_challenge_create", challenge.get_json())
    accepted = client.post(f"/api/v1/challenges/{challenge.json['id']}/accept", headers=headers_b)
    if accepted.status_code != 200:
        fail("api_challenge_accept", accepted.get_json())
    listed = client.get("/api/v1/challenges", headers=headers_b)
    if not listed.json.get("items"):
        fail("api_challenge_list", listed.get_json())
    detail = client.get(f"/api/v1/challenges/{challenge.json['id']}", headers=headers_b)
    if detail.status_code != 200 or len(detail.json.get("items", [])) != 5:
        fail("api_challenge_detail", detail.get_json())
    if any("correct" in item or "answer" in item for item in detail.json.get("items", [])):
        fail("api_challenge_answer_leak", detail.get_json())
    challenge_answers = [{"question_id": item["id"], "selected_index": 0, "elapsed_ms": 1000} for item in detail.json["items"]]
    submit_a = client.post(
        f"/api/v1/challenges/{challenge.json['id']}/submit", headers=headers_a,
        json={"answers": challenge_answers, "elapsed_sec": 50},
    )
    submit_b = client.post(
        f"/api/v1/challenges/{challenge.json['id']}/submit", headers=headers_b,
        json={"answers": challenge_answers, "elapsed_sec": 55},
    )
    if submit_a.status_code != 200 or submit_b.status_code != 200 or submit_b.json.get("status") != "completed":
        fail("api_challenge_scoring", {"owner": submit_a.get_json(), "opponent": submit_b.get_json()})
    ok("api_accounts_social", {
        "profiles_support_both_goals": True,
        "separate_diagnostic_records": True,
        "friend_request_accept": True,
        "challenge_invite_accept": True,
        "challenge_server_scoring": True,
    })

checks["summary"] = {
    "ok": all(item.get("ok") for item in checks["checks"].values()),
    "question_count": len(questions),
    "development_questions_release_eligible": release_eligible,
    "diagnostic_paths": ["qudrat", "tahsili"],
    "tahsili_model": "tahsili_common",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print("Suhail Sprint 54 validation: OK")
print(f"Checks: {len(checks['checks'])} | Questions: {len(questions)} | Report: {REPORT.relative_to(ROOT)}")
