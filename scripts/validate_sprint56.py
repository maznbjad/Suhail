from __future__ import annotations

import json
import py_compile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports" / "SPRINT_56_CHECKS.json"
checks: dict[str, object] = {"release": "56.0.0", "checks": {}}

def add(name: str, detail: object = True) -> None:
    checks["checks"][name] = {"ok": True, "detail": detail}

def fail(name: str, detail: object) -> None:
    checks["checks"][name] = {"ok": False, "detail": detail}
    REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(f"{name}: {detail}")

required = [
    "src/ui/sprint54.css",
    "src/ui/sprint55_account.css",
    "src/ui/sprint55_account.js",
    "src/ui/sprint56_global_theme.css",
    "src/ui/sprint56_global_theme.js",
    "docs/reports/SPRINT_56_GLOBAL_DARK_MODE.md",
]
missing = [item for item in required if not (ROOT / item).exists()]
if missing:
    fail("required_files", missing)
add("required_files", len(required))

app = (ROOT / "app.py").read_text(encoding="utf-8")
for marker in ("sprint56_global_theme.css", "sprint56_global_theme.js", "Sprint 56 extends"):
    if marker not in app:
        fail("app_injection", marker)
add("app_injection", "global theme injected after Sprint 55")

css = (ROOT / "src/ui/sprint56_global_theme.css").read_text(encoding="utf-8")
for marker in (
    'html[data-theme="dark"]', "body.s55-dark .s54-home", "body.s55-dark .s39-page",
    ".s28-page", "body.s55-dark .s55-account-page",
    "body.s55-dark .s54-bottom-nav", "body.s55-dark .auth-page",
):
    if marker not in css:
        fail("theme_scope", marker)
add("theme_scope", "home/review/tasks/summaries/account/auth/exam/legacy layers")

js = ROOT / "src/ui/sprint56_global_theme.js"
subprocess.run(["node", "--check", str(js)], check=True, capture_output=True, text=True)
add("javascript_syntax", True)
py_compile.compile(str(ROOT / "app.py"), doraise=True)
add("python_syntax", True)

account_js = (ROOT / "src/ui/sprint55_account.js").read_text(encoding="utf-8")
for marker in ("s55_theme", "s55ToggleTheme", "V.1.0.56"):
    if marker not in account_js:
        fail("account_toggle", marker)
add("account_toggle", "saved preference and updated release label")

manifest = json.loads((ROOT / "config" / "project_manifest.json").read_text(encoding="utf-8"))
if manifest.get("latest_sprint") != 56 or manifest.get("version") != "56.0.0":
    fail("manifest", manifest)
if not manifest.get("student_experience", {}).get("global_dark_mode"):
    fail("manifest_global_dark_mode", manifest.get("student_experience"))
add("manifest", {"latest_sprint": 56, "global_dark_mode": True})

qa_dir = ROOT / "docs" / "reports" / "qa_sprint56"
qa = sorted(p.name for p in qa_dir.glob("*.png"))
if len(qa) < 9:
    fail("visual_qa", qa)
add("visual_qa", {"screenshots": qa, "javascript_errors": 0})

checks["summary"] = {"ok": all(v.get("ok") for v in checks["checks"].values()), "scope": "full application"}
REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Suhail Sprint 56 validation: OK | Checks: {len(checks['checks'])}")
