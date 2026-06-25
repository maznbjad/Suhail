from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_static() -> None:
    manifest = json.loads((ROOT / "config/project_manifest.json").read_text(encoding="utf-8"))
    assert manifest["latest_sprint"] == 114
    assert manifest["student_experience"]["group_challenge"]["maximum_players"] == 10
    assert manifest["student_experience"]["group_challenge"]["question_time_sec"] == 30
    assert not list((ROOT / "assets/summary_pdfs").glob("*_ocr.json"))
    for name in (
        "sprint112_friends.js", "sprint113_group_challenge.js", "sprint114_legal_qa.js",
        "sprint112_friends.css", "sprint113_group_challenge.css", "sprint114_legal_qa.css",
    ):
        assert (ROOT / "src/ui" / name).is_file(), name
    assert (ROOT / "data/legal/terms_ar.md").is_file()
    assert (ROOT / "data/legal/privacy_ar.md").is_file()


def check_api_flow() -> None:
    import src.api.server as server

    temp_db = Path(tempfile.mkdtemp(prefix="suhail114_")) / "test.db"
    shutil.copy2(ROOT / "data/suhail_learning.db", temp_db)
    server.DB_PATH = temp_db
    app = server.create_app()
    app.testing = True

    def register(index: int):
        client = app.test_client()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"s114_{index}@test.com",
                "username": f"s114user{index}",
                "display_name": f"طالب {index}",
                "password": "12345678",
            },
        )
        assert response.status_code == 201, response.json
        return client, response.json["token"]

    def headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    c1, t1 = register(1)
    c2, t2 = register(2)
    p2 = c2.get("/api/v1/profile", headers=headers(t2)).json["profile"]
    request = c1.post(
        "/api/v1/friend-requests",
        headers=headers(t1),
        json={"receiver_username": "s114user2"},
    )
    assert request.status_code == 201
    incoming = c2.get("/api/v1/friend-requests", headers=headers(t2)).json["incoming"]
    assert c2.post(
        f"/api/v1/friend-requests/{incoming[0]['id']}/respond",
        headers=headers(t2),
        json={"action": "accept"},
    ).status_code == 200
    room = c1.post(
        "/api/v1/group-challenges",
        headers=headers(t1),
        json={"exam": "قدرات كمي", "question_count": 5, "friend_codes": [p2["friend_code"]]},
    )
    assert room.status_code == 201, room.json
    room_id = room.json["id"]
    assert room.json["maximum_players"] == 10
    assert room.json["question_time_sec"] == 30
    assert c2.post(
        f"/api/v1/group-challenges/{room_id}/respond",
        headers=headers(t2),
        json={"action": "accept"},
    ).status_code == 200
    assert c1.post(
        f"/api/v1/group-challenges/{room_id}/start",
        headers=headers(t1),
        json={},
    ).status_code == 200

    with sqlite3.connect(temp_db) as connection:
        question_ids = json.loads(
            connection.execute(
                "SELECT question_ids_json FROM group_challenges WHERE id = ?", (room_id,)
            ).fetchone()[0]
        )
        question = json.loads(
            connection.execute(
                "SELECT payload_json FROM questions WHERE id = ?", (question_ids[0],)
            ).fetchone()[0]
        )
    correct = int(question["correct"])
    result = c1.post(
        f"/api/v1/group-challenges/{room_id}/answer",
        headers=headers(t1),
        json={"question_index": 0, "selected_index": correct},
    )
    assert result.status_code == 200
    assert result.json["won_point"] is True
    assert result.json["state"]["current_index"] == 1


if __name__ == "__main__":
    check_static()
    check_api_flow()
    print("Sprint 114 validation passed.")
