"""Validate Sprint 71 exam stability, feedback modes and unified summaries."""
from __future__ import annotations

import ast
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
S59 = ROOT / "src" / "ui" / "sprint59_summaries_navigation.js"
S68 = ROOT / "src" / "ui" / "sprint68_feedback_control.js"
S69 = ROOT / "src" / "ui" / "sprint69_summary_knowledge.js"
S70 = ROOT / "src" / "ui" / "sprint70_unified_app.js"
S70_CSS = ROOT / "src" / "ui" / "sprint70_unified_app.css"
S71 = ROOT / "src" / "ui" / "sprint71_exam_summary_unification.js"
S71_CSS = ROOT / "src" / "ui" / "sprint71_exam_summary_unification.css"
API = ROOT / "src" / "api" / "server.py"
QUESTIONS = ROOT / "data" / "questions.json"
SUMMARIES = ROOT / "data" / "smart_summaries.json"


def node_ok(path: Path) -> bool:
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    return result.returncode == 0


source = APP.read_text(encoding="utf-8")
s59 = S59.read_text(encoding="utf-8")
s68 = S68.read_text(encoding="utf-8")
s69 = S69.read_text(encoding="utf-8")
s70 = S70.read_text(encoding="utf-8")
s70_css = S70_CSS.read_text(encoding="utf-8")
s71 = S71.read_text(encoding="utf-8")
s71_css = S71_CSS.read_text(encoding="utf-8")
api = API.read_text(encoding="utf-8")
questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
summaries = json.loads(SUMMARIES.read_text(encoding="utf-8"))
counts = Counter(str(q.get("exam", "")) for q in questions)
subjects = Counter(str(q.get("subject", "")) for q in questions if q.get("exam") == "تحصيلي")

try:
    ast.parse(source)
    python_syntax = True
except SyntaxError:
    python_syntax = False

checks = {
    "python_syntax": python_syntax,
    "javascript_syntax": all(node_ok(p) for p in (S59, S68, S69, S70, S71)),
    "sprint71_loaded_after_sprint70": source.find("Sprint 71 is the final exam-stability") > source.find("Sprint 70 is the final ownership"),
    "sprint71_assets_injected": "sprint71_exam_summary_unification.css" in source and "sprint71_exam_summary_unification.js" in source,
    "exam_class_watchdog": "s71-exam-active" in s71 and "stabilizeExam" in s71,
    "unanswered_choices_enabled": "if(!result?.answered)button.disabled=false" in s71,
    "next_locked_until_answer": "next.disabled=!result?.answered" in s71,
    "feedback_default_off": "const KEY='suhail_show_answer_result'" in s68 and "window.SUHAIL_SHOW_RESULT=v" in s68,
    "feedback_off_auto_advance": "answeredIndex<activeQuestions.length-1" in s68 and "nextQuiz" in s68,
    "feedback_on_direct_result": "directFeedback" in s68 and "box.style.display='block'" in s68,
    "feedback_observer_debounced": "observerTimer" in s68 and "setTimeout(()=>{patch();ensureToggle()},25)" in s68,
    "linked_summary_loop_fixed": "s69Signature" in s69 and "box.dataset.s69Signature===signature" in s69 and "observerTimer" in s69,
    "navigation_style_loop_fixed": "attributeFilter: ['class']" in s70 and "attributeFilter: ['style']" not in s70,
    "navigation_hidden_by_class": "s70-force-hidden" in s70 and "#s54BottomNav.s70-force-hidden" in s70_css,
    "old_summary_renderer_guarded": "if(window.SuhailSprint71)return;" in s59,
    "stable_unit_renderer": "s17OpenUnitStable" in source and "s17StableRenderer" in source and "s17OpenUnitStable" in s71,
    "three_summary_paths": all(text in s71 for text in ("تحصيلي", "قدرات كمي", "قدرات لفظي")),
    "four_tahsili_subjects": all(text in s71 for text in ("فيزياء", "كيمياء", "رياضيات", "الأحياء وعلم البيئة")),
    "one_menu_component": "function card(" in s71 and "s71-menu-card" in s71 and "s71-menu-card" in s71_css,
    "unit_search": "s71UnitSearch" in s71 and "s71FilterUnits" in s71,
    "dark_menu_surface": "body.s55-dark .s71-menu-card" in s71_css and "#112130" in s70_css,
    "dark_text_contrast_tokens": "#f4f9fd" in s71_css and "#a9bfce" in s71_css,
    "api_release_71": 'RELEASE = "71.0.0"' in api,
    "question_total": len(questions),
    "question_counts": dict(counts),
    "smart_summary_total": len(summaries),
    "biology_name_unified": "أحياء" not in subjects and subjects.get("الأحياء وعلم البيئة", 0) > 0,
}

expected = {"قدرات كمي": 1500, "قدرات لفظي": 1500, "تحصيلي": 2400}
boolean_keys = [key for key, value in checks.items() if isinstance(value, bool)]
checks["passed"] = (
    all(checks[key] for key in boolean_keys)
    and checks["question_total"] == 5400
    and checks["question_counts"] == expected
    and checks["smart_summary_total"] == 72
)

report = ROOT / "docs" / "reports" / "SPRINT_71_CHECKS.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
raise SystemExit(0 if checks["passed"] else 1)
