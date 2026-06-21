#!/usr/bin/env python3
"""Audit and repair deterministic development questions.

This script only auto-repairs rules that can be proven from the question text.
Everything else remains marked for human editorial review before production.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "questions.json"
REPORT = ROOT / "docs" / "reports" / "SPRINT_50_QUESTION_AUDIT.json"

PERCENT_RE = re.compile(r"كم يساوي\s+(\d+(?:\.\d+)?)%\s+من\s+(\d+(?:\.\d+)?)؟")


def format_number(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def audit(repair: bool = True) -> dict:
    questions = json.loads(BANK.read_text(encoding="utf-8"))
    issues: list[dict] = []
    repaired = 0
    ids = Counter(str(q.get("id", "")) for q in questions)

    for q in questions:
        qid = str(q.get("id", ""))
        if not qid:
            issues.append({"id": qid, "severity": "error", "code": "missing_id"})
        elif ids[qid] > 1:
            issues.append({"id": qid, "severity": "error", "code": "duplicate_id"})

        choices = [str(x) for x in q.get("choices", [])]
        correct_index = q.get("correct")
        if len(choices) != 4 or len(set(choices)) != 4:
            issues.append({"id": qid, "severity": "error", "code": "invalid_choices"})
        if not isinstance(correct_index, int) or not 0 <= correct_index < len(choices):
            issues.append({"id": qid, "severity": "error", "code": "invalid_correct_index"})
        elif str(q.get("answer", "")) != choices[correct_index]:
            issues.append({"id": qid, "severity": "error", "code": "answer_index_mismatch"})

        match = PERCENT_RE.fullmatch(str(q.get("question", "")).strip())
        if match:
            pct = Decimal(match.group(1))
            base = Decimal(match.group(2))
            expected = format_number(base * pct / Decimal(100))
            actual = str(q.get("answer", ""))
            if expected != actual:
                issues.append({
                    "id": qid,
                    "severity": "error",
                    "code": "percentage_truncation",
                    "actual": actual,
                    "expected": expected,
                })
                if repair:
                    old_choices = choices
                    distractors = [x for x in old_choices if x != actual and x != expected]
                    numeric = Decimal(expected)
                    candidates = [
                        format_number(numeric + Decimal(2)),
                        format_number(max(Decimal("0.1"), numeric - Decimal(2))),
                        format_number(base - numeric),
                    ]
                    new_choices = [expected]
                    for candidate in distractors + candidates:
                        if candidate not in new_choices:
                            new_choices.append(candidate)
                        if len(new_choices) == 4:
                            break
                    q["choices"] = new_choices
                    q["correct"] = 0
                    q["answer"] = expected
                    q["explain"] = f"نحوّل {format_number(pct)}% إلى {format_number(pct / Decimal(100))} ثم نضربها في {format_number(base)}، فيكون الناتج {expected}."
                    q["auto_validation"] = "percentage_exact_v1"
                    repaired += 1

        required = ["exam", "category", "skill", "question", "choices", "explain"]
        missing = [field for field in required if not q.get(field)]
        if missing:
            issues.append({"id": qid, "severity": "warning", "code": "missing_fields", "fields": missing})

        q.setdefault("editorial_status", "needs_review")
        q.setdefault("release_eligible", False)
        q.setdefault("rights_status", "unverified")

    if repair:
        BANK.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "release": "54.0.0",
        "question_count": len(questions),
        "unique_ids": len(ids),
        "auto_repaired": repaired,
        "errors": sum(1 for x in issues if x["severity"] == "error"),
        "warnings": sum(1 for x in issues if x["severity"] == "warning"),
        "release_eligible": sum(1 for q in questions if q.get("release_eligible") is True),
        "development_only": sum(1 for q in questions if q.get("release_eligible") is not True),
        "issues": issues,
        "note": "Auto-repair is limited to mathematically provable templates. Human pedagogical, linguistic and rights review is still required.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = audit(repair=True)
    print(json.dumps({k: result[k] for k in ("question_count", "auto_repaired", "errors", "warnings", "release_eligible")}, ensure_ascii=False))
