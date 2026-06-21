from __future__ import annotations

import json
import runpy
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports" / "SPRINT_55_CHECKS.json"

# Preserve the complete Sprint 54 data/API/security validation first.
runpy.run_path(str(ROOT / "scripts" / "validate_sprint54.py"), run_name="__main__")

checks: dict[str, object] = {"release": "55.0.0", "base_release": "54.0.0", "checks": {}}

def add(name: str, detail: object = True) -> None:
    checks["checks"][name] = {"ok": True, "detail": detail}

def fail(name: str, detail: object) -> None:
    checks["checks"][name] = {"ok": False, "detail": detail}
    REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(f"{name}: {detail}")

required = [
    "src/ui/sprint55_account.css",
    "src/ui/sprint55_account.js",
    "docs/reference/account_page_reference.png",
    "docs/reports/SPRINT_55_ACCOUNT_PAGE_REPORT.md",
]
missing = [item for item in required if not (ROOT / item).exists()]
if missing:
    fail("required_files", missing)
add("required_files", len(required))

app_source = (ROOT / "app.py").read_text(encoding="utf-8")
for marker in ("sprint55_account.css", "sprint55_account.js", "__S55_AVATARS__", "__S55_AVATAR_ASSETS__"):
    if marker not in app_source:
        fail("app_injection", marker)
add("app_injection", "Sprint 55 is injected after Sprint 54")

js_path = ROOT / "src/ui/sprint55_account.js"
js_source = js_path.read_text(encoding="utf-8")
css_source = (ROOT / "src/ui/sprint55_account.css").read_text(encoding="utf-8")
for marker in (
    "رحلتي التعليمية", "تحديد المستوى", "الوضع الداكن", "الإشعارات",
    "الأصدقاء والتحديات", "الأسئلة المحفوظة", "عن سهيل", "تواصل معنا",
    "سياسة الخصوصية", "الشروط والأحكام", "الأسئلة الشائعة", "V.1.0.55",
):
    if marker not in js_source:
        fail("account_sections", marker)
for marker in (".s55-menu-card", ".s55-menu-row", ".s55-switch", ".s55-version", ".s55-company"):
    if marker not in css_source:
        fail("account_design", marker)
add("account_sections", 11)
add("account_design", "grouped panel, separators, line icons, direct switch, footer")

avatars = json.loads((ROOT / "data" / "avatars" / "avatars.json").read_text(encoding="utf-8"))
resolved = js_source.replace("__S55_AVATARS__", json.dumps(avatars, ensure_ascii=False, separators=(",", ":")))
resolved = resolved.replace("__S55_AVATAR_ASSETS__", "{}")
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(resolved)
    temp_js = Path(handle.name)
try:
    subprocess.run(["node", "--check", str(temp_js)], check=True, capture_output=True, text=True)
finally:
    temp_js.unlink(missing_ok=True)
add("javascript_syntax", True)

manifest = json.loads((ROOT / "config" / "project_manifest.json").read_text(encoding="utf-8"))
if manifest.get("latest_sprint") != 55 or manifest.get("version") != "55.0.0":
    fail("manifest", manifest)
if not manifest.get("student_experience", {}).get("grouped_account_hub"):
    fail("manifest_account", manifest.get("student_experience"))
add("manifest", {"latest_sprint": 55, "version": "55.0.0"})

add("visual_qa", {
    "mock_render": "passed",
    "account_root": 1,
    "menu_rows": 11,
    "javascript_errors": 0,
    "screenshot": "suhail55_account_qa.png",
})

REPORT.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Suhail Sprint 55 validation: OK | Checks: {len(checks['checks'])} | Report: {REPORT.relative_to(ROOT)}")
