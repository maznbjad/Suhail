#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except Exception:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data" / "questions.json"
ARCHIVE = ROOT / "data" / "archive" / "questions_development_seed_s57.json"
DB = ROOT / "data" / "suhail_learning.db"
REPORT = ROOT / "docs" / "reports" / "SPRINT_58_CHECKS.json"

checks: dict[str, Any] = {}
errors: list[str] = []
warnings: list[str] = []


def expect(name: str, condition: bool, detail: Any = None) -> None:
    checks[name] = {"passed": bool(condition), "detail": detail}
    if not condition:
        errors.append(name)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


questions = load_json(QUESTIONS)
expect("questions_is_list", isinstance(questions, list), type(questions).__name__)
expect("question_count_280", len(questions) == 280, len(questions))

by_exam = Counter(q.get("exam") for q in questions)
expect("quant_count_195", by_exam.get("قدرات كمي") == 195, dict(by_exam))
expect("verbal_count_85", by_exam.get("قدرات لفظي") == 85, dict(by_exam))

ids = [str(q.get("id", "")) for q in questions]
expect("unique_nonempty_ids", len(ids) == len(set(ids)) and all(ids), len(set(ids)))
question_pairs = [(str(q.get("question", "")).strip(), str(q.get("passage", "")).strip()) for q in questions]
expect("unique_question_passage_pairs", len(question_pairs) == len(set(question_pairs)), len(set(question_pairs)))

position_distribution = [0, 0, 0, 0]
question_errors: list[dict[str, Any]] = []
for q in questions:
    qid = str(q.get("id", ""))
    choices = q.get("choices")
    correct = q.get("correct")
    if not isinstance(choices, list) or len(choices) != 4:
        question_errors.append({"id": qid, "issue": "choices_must_be_four"})
        continue
    normalized = [str(item).strip() for item in choices]
    if len(set(normalized)) != 4 or any(not item for item in normalized):
        question_errors.append({"id": qid, "issue": "choices_must_be_unique_nonempty"})
    if not isinstance(correct, int) or not 0 <= correct <= 3:
        question_errors.append({"id": qid, "issue": "invalid_correct_index"})
        continue
    position_distribution[correct] += 1
    if str(q.get("answer", "")).strip() != normalized[correct]:
        question_errors.append({"id": qid, "issue": "answer_does_not_match_choice"})
    if not str(q.get("explain", "")).strip():
        question_errors.append({"id": qid, "issue": "missing_explanation"})
    if q.get("test_format") != "محوسب" or q.get("delivery_mode") != "computerized":
        question_errors.append({"id": qid, "issue": "not_computerized"})
    for key in ("concept_id", "keywords", "source_documents", "copyright_method", "editorial_status"):
        if not q.get(key):
            question_errors.append({"id": qid, "issue": f"missing_{key}"})

expect("question_schema_and_answers", not question_errors, question_errors[:20])
expect("balanced_correct_positions", position_distribution == [70, 70, 70, 70], position_distribution)
expect("all_computerized_no_paper", all(q.get("test_format") == "محوسب" for q in questions), sorted(set(q.get("test_format") for q in questions)))

images = [str(q.get("image")) for q in questions if q.get("image")]
missing_images: list[str] = []
broken_svgs: list[str] = []
for rel in images:
    path = ROOT / rel
    if not path.exists():
        missing_images.append(rel)
        continue
    try:
        ET.parse(path)
    except Exception as exc:
        broken_svgs.append(f"{rel}: {exc}")
expect("diagram_count_21", len(images) == 21, len(images))
expect("all_diagrams_exist", not missing_images, missing_images)
expect("all_svgs_parse", not broken_svgs, broken_svgs)

archive = load_json(ARCHIVE)
expect("development_seed_archived_1000", isinstance(archive, list) and len(archive) == 1000, len(archive) if isinstance(archive, list) else None)

with sqlite3.connect(DB) as connection:
    db_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    db_by_exam = dict(connection.execute("SELECT exam, COUNT(*) FROM questions GROUP BY exam").fetchall())
    db_ids = [row[0] for row in connection.execute("SELECT id FROM questions ORDER BY id").fetchall()]
expect("sqlite_count_matches", db_count == 280, db_count)
expect("sqlite_exam_counts_match", db_by_exam == {"قدرات كمي": 195, "قدرات لفظي": 85}, db_by_exam)
expect("sqlite_ids_match_json", sorted(ids) == db_ids, len(db_ids))

avatars = load_json(ROOT / "data" / "avatars" / "avatars.json")
items = avatars.get("items", []) if isinstance(avatars, dict) else []
expect("eight_avatars", len(items) == 8, len(items))
expect("avatar_names_hidden", all(not str(item.get("name", "")).strip() and not str(item.get("name_ar", "")).strip() for item in items), [(i.get("id"), i.get("name"), i.get("name_ar")) for i in items])
expect("avatar_gender_split", Counter(i.get("gender_key") for i in items) == {"male": 4, "female": 4}, dict(Counter(i.get("gender_key") for i in items)))

female_variants = [ROOT / "assets" / "avatars" / "generated" / f"female_01_{kind}.webp" for kind in ("card", "avatar", "half", "full")]
variant_details: dict[str, Any] = {}
variants_ok = True
for path in female_variants:
    if not path.exists():
        variants_ok = False
        variant_details[path.name] = "missing"
        continue
    if Image is not None:
        with Image.open(path) as image:
            variant_details[path.name] = {"size": list(image.size), "mode": image.mode}
            # The corrected crop should retain visible breathing room above the head.
            top_band = image.convert("RGBA").crop((0, 0, image.width, max(1, int(image.height * 0.035))))
            alpha = top_band.getchannel("A")
            alpha_values = alpha.get_flattened_data() if hasattr(alpha, "get_flattened_data") else alpha.getdata()
            transparent_ratio = sum(1 for px in alpha_values if px < 16) / max(1, alpha.width * alpha.height)
            variant_details[path.name]["transparent_top_ratio"] = round(transparent_ratio, 4)
            if transparent_ratio < 0.65:
                warnings.append(f"{path.name}: top breathing room is lower than expected")
expect("female_01_variants_exist", variants_ok, variant_details)

app_text = (ROOT / "app.py").read_text(encoding="utf-8")
js_text = (ROOT / "src" / "ui" / "sprint58_question_bank.js").read_text(encoding="utf-8")
css_text = (ROOT / "src" / "ui" / "sprint58_question_bank.css").read_text(encoding="utf-8")
expect("sprint58_assets_injected", "sprint58_question_bank.css" in app_text and "sprint58_question_bank.js" in app_text, None)
expect("paper_mode_disabled_until_sources", "يُفعّل عند إضافة التجميعات الورقية" in js_text and "disabled" in js_text, None)
expect("question_ui_responsive", "@media" in css_text and ".s58-progress-wrap" in css_text and ".question-passage" in css_text, None)
expect("version_58_present", "58.0.0" in js_text and "58.0.0" in (ROOT / "src" / "api" / "server.py").read_text(encoding="utf-8"), None)

commands = [
    [sys.executable, "-m", "py_compile", str(ROOT / "app.py"), str(ROOT / "src" / "api" / "server.py")],
    ["node", "--check", str(ROOT / "src" / "ui" / "sprint58_question_bank.js")],
    ["node", "--check", str(ROOT / "src" / "ui" / "sprint54_experience.js")],
    ["node", "--check", str(ROOT / "src" / "ui" / "sprint55_account.js")],
]
command_results = []
for command in commands:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        command_results.append({"command": command, "returncode": result.returncode, "stderr": result.stderr[-2000:]})
    except Exception as exc:
        command_results.append({"command": command, "returncode": -1, "stderr": str(exc)})
expect("python_and_javascript_syntax", all(item["returncode"] == 0 for item in command_results), command_results)

report = {
    "release": "58.0.0",
    "qa_passed": not errors,
    "errors": errors,
    "warnings": warnings,
    "checks": checks,
    "summary": {
        "questions": len(questions),
        "quantitative": by_exam.get("قدرات كمي", 0),
        "verbal": by_exam.get("قدرات لفظي", 0),
        "diagrams": len(images),
        "correct_position_distribution": position_distribution,
        "archived_development_questions": len(archive) if isinstance(archive, list) else 0,
    },
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report["qa_passed"] else 1)
