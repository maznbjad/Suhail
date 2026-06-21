from __future__ import annotations

import json
import py_compile
import subprocess
import tempfile
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT = ROOT / "docs" / "reports" / "SPRINT_57_CHECKS.json"
checks: dict[str, object] = {"release": "57.0.0", "checks": {}}


def add(name: str, detail: object = True) -> None:
    checks["checks"][name] = {"ok": True, "detail": detail}


def fail(name: str, detail: object) -> None:
    checks["checks"][name] = {"ok": False, "detail": detail}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(f"{name}: {detail}")

required = [
    "data/avatars/avatars.json",
    "src/ui/sprint54_experience.js",
    "src/ui/sprint54.css",
    "src/ui/sprint55_account.js",
    "src/api/server.py",
    "src/core/challenge_repository.py",
    "docs/reports/SPRINT_57_CHARACTER_SYSTEM.md",
]
missing = [item for item in required if not (ROOT / item).exists()]
if missing:
    fail("required_files", missing)
add("required_files", len(required))

catalog = json.loads((ROOT / "data" / "avatars" / "avatars.json").read_text(encoding="utf-8"))
items = [item for item in catalog.get("items", []) if item.get("enabled", True)]
if len(items) != 8:
    fail("avatar_count", len(items))
ids = [item["id"] for item in items]
if len(ids) != len(set(ids)):
    fail("avatar_ids_unique", ids)
male = [item for item in items if item.get("gender_key") == "male"]
female = [item for item in items if item.get("gender_key") == "female"]
if len(male) != 4 or len(female) != 4:
    fail("gender_groups", {"male": len(male), "female": len(female)})
add("catalog", {"total": 8, "male": 4, "female": 4, "default": catalog.get("default")})

expected_sizes = {
    "card_asset": (320, 420),
    "avatar_asset": (240, 240),
    "half_asset": (420, 520),
    "full_asset": (640, 900),
}
asset_details = []
for item in items:
    for field, expected in expected_sizes.items():
        rel = item.get(field)
        if not rel:
            fail("asset_catalog_paths", {"id": item["id"], "field": field})
        path = ROOT / rel
        if not path.exists():
            fail("asset_exists", str(rel))
        with Image.open(path) as image:
            if image.size != expected:
                fail("asset_dimensions", {"path": str(rel), "actual": image.size, "expected": expected})
            if image.format != "WEBP":
                fail("asset_format", {"path": str(rel), "format": image.format})
        asset_details.append({"id": item["id"], "variant": field, "bytes": path.stat().st_size})
add("avatar_assets", {"count": len(asset_details), "bytes": sum(x["bytes"] for x in asset_details)})

app = (ROOT / "app.py").read_text(encoding="utf-8")
for marker in (
    'id="registerGender"',
    "selectRegisterGender",
    "__S54_AVATAR_PORTRAIT_ASSETS__",
    "__S54_AVATAR_HALF_ASSETS__",
    "__S54_AVATAR_FULL_ASSETS__",
):
    if marker not in app:
        fail("app_injection", marker)
add("app_injection", "registration gender plus four runtime avatar maps")

ui = (ROOT / "src" / "ui" / "sprint54_experience.js").read_text(encoding="utf-8")
for marker in (
    "const VERSION='57.0.0'",
    "function avatarItems(gender)",
    "s54SetupGender",
    "defaultAvatarFor",
    "avatarItems(setupDraft.gender)",
):
    if marker not in ui:
        fail("ui_gender_filter", marker)
add("ui_gender_filter", "four matching characters shown after account gender choice")

css = (ROOT / "src" / "ui" / "sprint54.css").read_text(encoding="utf-8")
for marker in (".s54-gender-choice", ".s54-avatar-grid", ".s54-avatar-option"):
    if marker not in css:
        fail("character_design", marker)
add("character_design", "2x2 character cards and gender selector")

api = (ROOT / "src" / "api" / "server.py").read_text(encoding="utf-8")
repo = (ROOT / "src" / "core" / "challenge_repository.py").read_text(encoding="utf-8")
for marker in ("avatar_gender_mismatch", 'RELEASE = "57.0.0"'):
    if marker not in api:
        fail("api_gender_validation", marker)
if "gender TEXT NOT NULL DEFAULT 'male'" not in repo:
    fail("profile_gender_schema", "missing gender column")
add("api_and_schema", "gender persisted and avatar mismatch rejected")

# Exercise the profile endpoint against a temporary database so validation never touches delivery data.
from src.api import server as api_server
with tempfile.TemporaryDirectory() as temp_dir:
    api_server.DB_PATH = Path(temp_dir) / "sprint57_gender.db"
    test_app = api_server.create_app()
    test_app.testing = True
    client = test_app.test_client()
    registered = client.post("/api/v1/auth/register", json={
        "email": "sprint57.qa@suhail.test",
        "password": "12345678",
        "display_name": "QA",
    })
    if registered.status_code != 201:
        fail("api_gender_runtime", {"register": registered.status_code, "body": registered.get_json()})
    token = registered.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    accepted = client.put("/api/v1/profile", headers=headers, json={
        "display_name": "QA",
        "academic_track": "scientific",
        "gender": "female",
        "exam_goals": ["qudrat", "tahsili"],
        "avatar_id": "female_02",
    })
    rejected = client.put("/api/v1/profile", headers=headers, json={
        "display_name": "QA",
        "academic_track": "scientific",
        "gender": "female",
        "exam_goals": ["qudrat"],
        "avatar_id": "male_01",
    })
    if accepted.status_code != 200 or accepted.get_json().get("profile", {}).get("gender") != "female":
        fail("api_gender_runtime", {"accepted": accepted.status_code, "body": accepted.get_json()})
    if rejected.status_code != 400 or rejected.get_json().get("error") != "avatar_gender_mismatch":
        fail("api_gender_runtime", {"rejected": rejected.status_code, "body": rejected.get_json()})
add("api_gender_runtime", {"matching_avatar": 200, "mismatched_avatar": 400})

for py_file in (ROOT / "app.py", ROOT / "src" / "api" / "server.py", ROOT / "src" / "core" / "challenge_repository.py"):
    py_compile.compile(str(py_file), doraise=True)
for js_file in (ROOT / "src" / "ui" / "sprint54_experience.js", ROOT / "src" / "ui" / "sprint55_account.js"):
    subprocess.run(["node", "--check", str(js_file)], check=True, capture_output=True, text=True)
add("syntax", {"python": True, "javascript": True})

manifest = json.loads((ROOT / "config" / "project_manifest.json").read_text(encoding="utf-8"))
if manifest.get("latest_sprint") != 57 or manifest.get("version") != "57.0.0":
    fail("manifest", manifest)
experience = manifest.get("student_experience", {})
if experience.get("avatar_groups") != {"male": 4, "female": 4} or not experience.get("avatar_gender_filtering"):
    fail("manifest_avatar_system", experience)
add("manifest", {"latest_sprint": 57, "gender_filtering": True})

qa_dir = ROOT / "docs" / "reports" / "qa_sprint57"
qa = sorted(p.name for p in qa_dir.glob("*.*"))
if len(qa) < 4:
    fail("visual_qa", qa)
add("visual_qa", qa)

checks["summary"] = {
    "ok": all(value.get("ok") for value in checks["checks"].values()),
    "scope": "8 production character assets, account gender filtering, persistence, and API guard",
}
REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Suhail Sprint 57 validation: OK | Checks: {len(checks['checks'])}")
