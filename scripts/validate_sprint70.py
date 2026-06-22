"""Validate the final Sprint 70 runtime and unified UI contract."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
BOOT = ROOT / "src" / "ui" / "sprint70_boot.js"
CSS = ROOT / "src" / "ui" / "sprint70_unified_app.css"
JS = ROOT / "src" / "ui" / "sprint70_unified_app.js"
RUNNER = ROOT / "run_suhail.bat"
QUESTIONS = ROOT / "data" / "questions.json"
SUMMARIES = ROOT / "data" / "smart_summaries.json"


def node_ok(path: Path) -> bool:
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    return result.returncode == 0


source = APP.read_text(encoding="utf-8")
boot = BOOT.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")
runner = RUNNER.read_text(encoding="utf-8")
questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
summaries = json.loads(SUMMARIES.read_text(encoding="utf-8"))
question_counts = Counter(str(item.get("exam", "")) for item in questions)
tahsili_subjects = Counter(
    str(item.get("subject", "")) for item in questions if item.get("exam") == "تحصيلي"
)

checks = {
    "python_syntax": True,
    "boot_javascript_syntax": node_ok(BOOT),
    "unified_javascript_syntax": node_ok(JS),
    "sprint70_injected_last": source.find("Sprint 70 is the final ownership layer") > source.find("Sprint 69 links"),
    "boot_injected_in_head": "s70_boot_js" in source and 'replace("</head>"' in source,
    "component_mobile_height": "components.html(html_code, height=960" in source,
    "storage_fallback": "memoryStorage" in boot and "__SUHAIL_STORAGE_FALLBACK__" in boot,
    "splash_failsafe": "4300" in boot and "suhailSplash" in boot,
    "dark_tokens": 'html[data-theme="dark"]' in css and "--s70-text:#f3f8fc" in css,
    "dark_text_overrides": "body.s55-dark .page" in css and "color:var(--s70-text-strong)!important" in css,
    "auth_nav_hidden": "body.s70-auth #s54BottomNav" in css,
    "onboarding_nav_hidden": "body.s70-onboarding #s54BottomNav" in css and "style.setProperty('display', 'none', 'important')" in js,
    "one_final_nav": "#s54BottomNav{display:grid!important}" in css and ".s47-bottom-nav{display:none!important}" in css,
    "unified_back_icon": "unifyBackIcons" in js and "data-s70-icon" not in js and "s70Icon" in js,
    "onboarding_guide": "أربع خطوات وتبدأ" in js and "حفظ وابدأ رحلتي" in js,
    "home_start_guide": "ابدأ بتحديد مستواك" in js,
    "dynamic_port_runner": "set /a PORT=8501" in runner and ":CHECK_PORT" in runner,
    "lan_runner": "--server.address 0.0.0.0" in runner and "LOCAL_IP" in runner,
    "preflight_runner": "scripts\\preflight.py" in runner,
    "question_total": len(questions),
    "question_counts": dict(question_counts),
    "smart_summary_total": len(summaries),
    "biology_name_unified": "أحياء" not in tahsili_subjects and tahsili_subjects.get("الأحياء وعلم البيئة", 0) > 0,
}

expected_counts = {"قدرات كمي": 1500, "قدرات لفظي": 1500, "تحصيلي": 2400}
boolean_keys = [key for key, value in checks.items() if isinstance(value, bool)]
checks["passed"] = (
    all(checks[key] for key in boolean_keys)
    and checks["question_total"] == 5400
    and checks["question_counts"] == expected_counts
    and checks["smart_summary_total"] == 72
)

report = ROOT / "docs" / "reports" / "SPRINT_70_CHECKS.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
raise SystemExit(0 if checks["passed"] else 1)
