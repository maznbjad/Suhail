"""Validate Sprint 59 summaries hierarchy and navigation contract."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
JS = ROOT / "src/ui/sprint59_summaries_navigation.js"
CSS = ROOT / "src/ui/sprint59_summaries_navigation.css"

source = APP.read_text(encoding="utf-8")
tree = ast.parse(source)
assignments: dict[str, list[dict]] = {}
for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    for target in node.targets:
        if isinstance(target, ast.Name) and target.id in {"fallback_summaries_data", "qiyas_summaries_seed"}:
            assignments[target.id] = ast.literal_eval(node.value)

base = assignments.get("fallback_summaries_data", [])
qiyas = assignments.get("qiyas_summaries_seed", [])
all_items = base + qiyas
exam_counts = Counter(str(x.get("exam", "")) for x in all_items)
tahsili_subject_counts = Counter(str(x.get("subject", "")) for x in base if x.get("exam") == "تحصيلي")
qiyas_subjects = {(x.get("exam"), x.get("subject")) for x in qiyas}

js = JS.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")

checks = {
    "python_syntax": True,
    "javascript_syntax": subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True).returncode == 0,
    "module_injected_after_sprint58": source.find("Sprint 59 restores") > source.find("Sprint 58 replaces"),
    "summary_total": len(all_items),
    "exam_counts": dict(exam_counts),
    "tahsili_subject_counts": dict(tahsili_subject_counts),
    "canonical_top_order": "exams:['تحصيلي','قدرات لفظي','قدرات كمي']" in js,
    "tahsili_only_contains_subjects": set(tahsili_subject_counts) == {"فيزياء", "كيمياء", "رياضيات", "أحياء"},
    "tahsili_subjects_have_18_each": all(tahsili_subject_counts.get(x) == 18 for x in ["فيزياء", "كيمياء", "رياضيات", "أحياء"]),
    "qudrat_subjects_not_mixed": qiyas_subjects == {("قدرات كمي", "كمي"), ("قدرات لفظي", "لفظي")},
    "bottom_nav_visible_in_summaries": "s54-mode-summary:not(.s54-auth-mode):not(.s59-exam-active) #s54BottomNav" in css,
    "bottom_nav_hidden_in_exam": "body.s59-exam-active #s54BottomNav" in css,
    "lift_nav_disabled": "#s54LiftNav,#s28LiftNav{display:none!important}" in css,
    "unified_back_icon": "s59-unified-back" in js and "s59-unified-back" in css,
    "search_min_two_chars": "q.length<2" in js,
    "physics_rich_path_preserved": "legacyOpenPhysics" in js,
    "related_questions_route": "s59OpenRelated" in js,
}

checks["passed"] = all(
    value is True
    for key, value in checks.items()
    if key not in {"summary_total", "exam_counts", "tahsili_subject_counts", "passed"}
)
checks["passed"] = checks["passed"] and checks["summary_total"] == 80 and checks["exam_counts"] == {
    "تحصيلي": 72,
    "قدرات كمي": 4,
    "قدرات لفظي": 4,
}

out = ROOT / "docs/reports/SPRINT_59_CHECKS.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
sys.exit(0 if checks["passed"] else 1)
