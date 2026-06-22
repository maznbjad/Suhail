from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARIES_PATH = ROOT / "data" / "smart_summaries.json"
QUESTIONS_PATH = ROOT / "data" / "questions.json"
MAP_PATH = ROOT / "data" / "content" / "summary_knowledge_map.json"
REPORT_PATH = ROOT / "docs" / "reports" / "SPRINT_69_KNOWLEDGE_LINK_REPORT.json"
DB_PATH = ROOT / "data" / "suhail_learning.db"

AR_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
NON_WORD = re.compile(r"[^\u0600-\u06FFa-zA-Z0-9]+")


def norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = AR_DIACRITICS.sub("", text)
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي"}))
    text = NON_WORD.sub(" ", text)
    return " ".join(text.split())


def compact_keywords(*parts: object) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        values = part if isinstance(part, list) else [part]
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            key = norm(text)
            if key and key not in seen:
                seen.add(key)
                out.append(text)
    return out[:24]


def block_id(order: int, kind: str, index: int) -> str:
    codes = {
        "idea": "IDEA",
        "definition": "DEF",
        "rule": "RULE",
        "relationship": "REL",
        "trap": "TRAP",
        "tip": "TIP",
        "example": "EX",
        "comparison": "CMP",
    }
    return f"PHY-{order:03d}-{codes[kind]}-{index:02d}"


def add_block(blocks: list[dict], summary: dict, kind: str, title: str, content: str,
              *, index: int = 1, keywords: list[str] | None = None, is_core: bool = False) -> None:
    content = str(content or "").strip()
    title = str(title or "").strip()
    if not content:
        return
    order = int(summary.get("order") or 0)
    base_keywords = compact_keywords(
        summary.get("title"), summary.get("unit"), summary.get("keywords", []), title, keywords or []
    )
    blocks.append({
        "id": block_id(order, kind, index),
        "summary_id": summary["id"],
        "subject": "فيزياء",
        "stage": summary.get("stage", ""),
        "unit": summary.get("unit", ""),
        "lesson": summary.get("title", ""),
        "type": kind,
        "title": title,
        "content": content,
        "keywords": base_keywords,
        "search_text": norm(" ".join(base_keywords + [content])),
        "order": len(blocks) + 1,
        "is_core": bool(is_core),
        "status": "published",
    })


def build_blocks(summary: dict) -> list[dict]:
    blocks: list[dict] = []
    add_block(blocks, summary, "idea", "الفكرة الجوهرية", summary.get("simple_idea", ""), is_core=True)

    for i, item in enumerate(summary.get("concept_map") or [], 1):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or f"تعريف {i}"
        description = item.get("description") or ""
        add_block(blocks, summary, "definition", title, description, index=i, keywords=[title], is_core=True)

    add_block(blocks, summary, "rule", "القاعدة أو القانون", summary.get("core_rule", ""), is_core=True)

    essence = summary.get("essence_buttons") or {}
    add_block(blocks, summary, "relationship", "العلاقة التي يجب فهمها", essence.get("relationship", ""), is_core=True)
    add_block(blocks, summary, "trap", "الفخ الشائع", essence.get("trap", ""), is_core=True)

    tips = [summary.get("simple_back", ""), summary.get("links_back", "")]
    for i, tip in enumerate(tips, 1):
        add_block(blocks, summary, "tip", "تلميح سهيل" if i == 1 else "تلميح إضافي", tip, index=i)

    example = summary.get("example") or {}
    if isinstance(example, dict):
        add_block(blocks, summary, "example", example.get("title") or "مثال", example.get("text", ""), is_core=True)

    for i, row in enumerate(summary.get("comparison") or [], 1):
        if not isinstance(row, dict):
            continue
        title = row.get("case") or f"مقارنة {i}"
        content = " — ".join(x for x in [row.get("effect"), row.get("example")] if x)
        add_block(blocks, summary, "comparison", title, content, index=i, keywords=[title])

    return blocks


# High-confidence mapping between the actual physics bank and the curated 72-summary set.
SKILL_TO_SUMMARY_ORDER = {
    "القياس": 2,
    "دقة القياس": 2,
    "المسافة": 4,
    "الإزاحة": 4,
    "السرعة المتجهة": 6,
    "السرعة المنتظمة": 6,
    "التسارع": 7,
    "التسارع المنتظم": 8,
    "مساحة منحنى السرعة الزمن": 8,
    "قانون نيوتن الأول": 11,
    "قانون نيوتن الثاني": 11,
    "قانون نيوتن الثالث": 11,
    "القوة المركزية": 17,
    "اتجاه القوة المركزية": 17,
    "عزم القوة": 22,
    "قوة الجاذبية": 20,
    "الزخم الخطي": 24,
    "الشغل": 26,
    "الطاقة الحركية": 28,
    "القدرة": 26,
    "الموجة الميكانيكية": 37,
    "سرعة الموجة": 37,
    "التردد": 36,
    "العلاقة بين التردد والدور": 36,
    "شدة الصوت": 39,
    "الانعكاس": 43,
    "قانون الانعكاس": 43,
    "الانكسار": 45,
    "شدة التيار": 54,
    "شدة التيار الكهربائي": 54,
    "فرق الجهد": 54,
    "المقاومة الكهربائية": 54,
    "قانون أوم": 54,
    "مقاومات على التوالي": 57,
    "المجال المغناطيسي": 58,
    "التأثير الكهروضوئي": 64,
    "الانشطار النووي": 71,
}

UNIT_FALLBACK = {
    "القياس": 2,
    "الحركة": 6,
    "القوى": 11,
    "الحركة الدائرية": 17,
    "الدوران": 22,
    "الجاذبية": 20,
    "الزخم": 24,
    "الشغل والطاقة": 26,
    "الموجات": 37,
    "الصوت": 39,
    "الضوء": 43,
    "الكهرباء": 54,
    "المغناطيسية": 58,
    "الفيزياء الحديثة": 64,
    "الفيزياء النووية": 71,
}


# Preferred exact block inside the target summary for each current physics skill.
SKILL_BLOCK_PREFERENCE = {
    "القياس": ("definition", "قياس"),
    "دقة القياس": ("definition", "دقة"),
    "المسافة": ("comparison", "المسافة"),
    "الإزاحة": ("definition", "إزاحة"),
    "السرعة المتجهة": ("idea", "السرعة"),
    "السرعة المنتظمة": ("rule", "القانون"),
    "التسارع": ("definition", "تسارع"),
    "التسارع المنتظم": ("idea", "الفكرة"),
    "مساحة منحنى السرعة-الزمن": ("example", "مثال"),
    "قانون نيوتن الأول": ("definition", "الأول"),
    "قانون نيوتن الثاني": ("definition", "الثاني"),
    "قانون نيوتن الثالث": ("definition", "الثالث"),
    "القوة المركزية": ("definition", "قوة مركزية"),
    "اتجاه القوة المركزية": ("trap", "الفخ"),
    "عزم القوة": ("rule", "القانون"),
    "قوة الجاذبية": ("rule", "القانون"),
    "الزخم الخطي": ("rule", "القانون"),
    "الشغل": ("definition", "شغل"),
    "الطاقة الحركية": ("definition", "طاقة حركة"),
    "القدرة": ("definition", "قدرة"),
    "الموجة الميكانيكية": ("idea", "الفكرة"),
    "سرعة الموجة": ("rule", "القانون"),
    "التردد": ("definition", "تردد"),
    "العلاقة بين التردد والدور": ("rule", "القانون"),
    "شدة الصوت": ("definition", "شدة"),
    "الانعكاس": ("idea", "الفكرة"),
    "قانون الانعكاس": ("rule", "القانون"),
    "الانكسار": ("idea", "الفكرة"),
    "شدة التيار": ("definition", "تيار"),
    "شدة التيار الكهربائي": ("definition", "تيار"),
    "فرق الجهد": ("definition", "جهد"),
    "المقاومة الكهربائية": ("definition", "مقاومة"),
    "قانون أوم": ("rule", "القانون"),
    "مقاومات على التوالي": ("comparison", "توالي"),
    "المجال المغناطيسي": ("idea", "الفكرة"),
    "التأثير الكهروضوئي": ("example", "مثال"),
    "الانشطار النووي": ("comparison", "انشطار"),
}

NORM_SKILL_TO_SUMMARY_ORDER = {norm(k): v for k, v in SKILL_TO_SUMMARY_ORDER.items()}
NORM_UNIT_FALLBACK = {norm(k): v for k, v in UNIT_FALLBACK.items()}
NORM_SKILL_BLOCK_PREFERENCE = {norm(k): v for k, v in SKILL_BLOCK_PREFERENCE.items()}


def choose_summary(question: dict, summaries_by_order: dict[int, dict]) -> tuple[dict | None, str]:
    skill = norm(question.get("skill"))
    unit = norm(question.get("unit"))
    if skill in NORM_SKILL_TO_SUMMARY_ORDER:
        return summaries_by_order.get(NORM_SKILL_TO_SUMMARY_ORDER[skill]), "skill_exact"
    if unit in NORM_UNIT_FALLBACK:
        return summaries_by_order.get(NORM_UNIT_FALLBACK[unit]), "unit_fallback"

    raw = norm(" ".join(str(question.get(k) or "") for k in ("skill", "unit", "question", "keywords")))
    best: tuple[int, dict | None] = (0, None)
    for summary in summaries_by_order.values():
        hay = norm(" ".join(compact_keywords(summary.get("title"), summary.get("unit"), summary.get("keywords", []))))
        score = sum(2 for token in hay.split() if len(token) > 2 and token in raw)
        if score > best[0]:
            best = (score, summary)
    return (best[1], "keyword_score") if best[0] >= 2 else (None, "unlinked")


def choose_block(question: dict, summary: dict) -> dict | None:
    blocks = summary.get("knowledge_blocks") or []
    if not blocks:
        return None
    skill = norm(question.get("skill"))
    preference = NORM_SKILL_BLOCK_PREFERENCE.get(skill)
    if preference:
        preferred_type, title_hint = preference
        hint = norm(title_hint)
        candidates = [b for b in blocks if b.get("type") == preferred_type]
        exact = next((b for b in candidates if hint and hint in norm(b.get("title"))), None)
        if exact:
            return exact
        if candidates:
            return candidates[0]

    qtext = norm(question.get("question"))
    scored: list[tuple[int, dict]] = []
    for block in blocks:
        score = 0
        btext = norm(" ".join([block.get("title", ""), block.get("content", ""), " ".join(block.get("keywords") or [])]))
        if skill and skill in btext:
            score += 12
        for token in skill.split():
            if len(token) > 2 and token in btext:
                score += 3
        for token in qtext.split():
            if len(token) > 3 and token in btext:
                score += 1
        if "تصف" in qtext and block.get("type") == "definition":
            score += 6
        if any(k in qtext for k in ("احسب", "اوجد", "يساوي", "مقدار", "قانون")) and block.get("type") == "rule":
            score += 5
        if block.get("type") == "idea":
            score += 2
        if block.get("is_core"):
            score += 1
        scored.append((score, block))
    scored.sort(key=lambda x: (x[0], -int(x[1].get("order", 0))), reverse=True)
    if scored and scored[0][0] > 0:
        return scored[0][1]
    return next((b for b in blocks if b.get("type") == "idea"), blocks[0])


def update_database(questions: list[dict]) -> dict:
    if not DB_PATH.exists():
        return {"updated": False, "reason": "database_missing"}
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    columns = {row[1] for row in cur.execute("PRAGMA table_info(questions)")}
    additions = {
        "summary_id": "TEXT",
        "summary_block_id": "TEXT",
        "linked_summary_title": "TEXT",
        "linked_block_title": "TEXT",
    }
    for name, sql_type in additions.items():
        if name not in columns:
            cur.execute(f"ALTER TABLE questions ADD COLUMN {name} {sql_type}")
    updated = 0
    for q in questions:
        if q.get("subject") != "فيزياء":
            continue
        cur.execute(
            "UPDATE questions SET summary_id=?, summary_block_id=?, linked_summary_title=?, linked_block_title=? WHERE id=?",
            (q.get("summary_id", ""), q.get("summary_block_id", ""), q.get("linked_summary_title", ""), q.get("linked_block_title", ""), q.get("id")),
        )
        updated += cur.rowcount
    con.commit()
    con.close()
    return {"updated": True, "rows": updated}


def main() -> None:
    summaries = json.loads(SUMMARIES_PATH.read_text(encoding="utf-8"))
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    knowledge_blocks: list[dict] = []
    summaries_by_order: dict[int, dict] = {}
    for summary in summaries:
        summary["summary_id"] = summary.get("id")
        blocks = build_blocks(summary)
        summary["knowledge_blocks"] = blocks
        summary["knowledge_block_count"] = len(blocks)
        summary["knowledge_schema_version"] = "1.0"
        knowledge_blocks.extend(blocks)
        summaries_by_order[int(summary.get("order") or 0)] = summary

    method_counts: Counter[str] = Counter()
    linked_by_summary: Counter[str] = Counter()
    linked_by_block_type: Counter[str] = Counter()
    unlinked: list[int] = []

    for q in questions:
        if q.get("subject") != "فيزياء":
            continue
        summary, method = choose_summary(q, summaries_by_order)
        method_counts[method] += 1
        if not summary:
            unlinked.append(int(q.get("public_id") or 0))
            continue
        block = choose_block(q, summary)
        q["summary_id"] = summary["id"]
        q["summary_exam"] = "تحصيلي"
        q["summary_subject"] = "فيزياء"
        q["summary_unit"] = summary.get("unit", "")
        q["summary_lesson"] = summary.get("title", "")
        q["summary_block_id"] = block.get("id", "") if block else ""
        q["linked_summary_title"] = summary.get("title", "")
        q["linked_block_title"] = block.get("title", "") if block else ""
        q["linked_block_excerpt"] = block.get("content", "")[:220] if block else ""
        trap_block = next((b for b in summary.get("knowledge_blocks", []) if b.get("type") == "trap"), None)
        q["misconception_block_id"] = trap_block.get("id", "") if trap_block else ""
        q["knowledge_link_method"] = method
        q["knowledge_link_status"] = "linked" if block else "summary_only"
        linked_by_summary[summary["id"]] += 1
        if block:
            linked_by_block_type[block["type"]] += 1

    SUMMARIES_PATH.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    QUESTIONS_PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")

    knowledge_map = {
        "schema_version": "1.0",
        "subject": "فيزياء",
        "summary_count": len(summaries),
        "block_count": len(knowledge_blocks),
        "blocks": knowledge_blocks,
    }
    MAP_PATH.write_text(json.dumps(knowledge_map, ensure_ascii=False, indent=2), encoding="utf-8")

    db_result = update_database(questions)
    physics_count = sum(1 for q in questions if q.get("subject") == "فيزياء")
    linked_count = physics_count - len(unlinked)
    report = {
        "summary_count": len(summaries),
        "knowledge_block_count": len(knowledge_blocks),
        "physics_question_count": physics_count,
        "linked_question_count": linked_count,
        "unlinked_question_count": len(unlinked),
        "link_rate_percent": round(linked_count * 100 / physics_count, 2) if physics_count else 0,
        "link_methods": dict(method_counts),
        "linked_by_block_type": dict(linked_by_block_type),
        "questions_per_summary_min": min(linked_by_summary.values()) if linked_by_summary else 0,
        "questions_per_summary_max": max(linked_by_summary.values()) if linked_by_summary else 0,
        "summaries_with_questions": len(linked_by_summary),
        "summaries_without_questions": [s["id"] for s in summaries if not linked_by_summary[s["id"]]],
        "unlinked_public_ids": unlinked[:100],
        "database": db_result,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
