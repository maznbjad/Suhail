#!/usr/bin/env python3
"""Upgrade all published physics summaries to the Sprint 79 mastery template.

The script deliberately keeps the approved source content and exact question links,
then reorganises every lesson into a beginner-friendly learning path. It does not
invent links to unpublished subjects or change the 5,400-question bank size.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SUMMARIES_PATH = ROOT / "data" / "smart_summaries.json"
SUMMARIES_SOURCE_PATH = ROOT / "data" / "content" / "sprint72_smart_summaries_source.json"
QUESTIONS_PATH = ROOT / "data" / "questions.json"
UNIT_ENRICHMENT_PATH = ROOT / "data" / "content" / "physics_unit_enrichment_s79.json"
KNOWLEDGE_MAP_PATH = ROOT / "data" / "content" / "summary_knowledge_map.json"
TEMPLATE_PATH = ROOT / "data" / "content" / "physics_lesson_template_v2.json"
REPORT_PATH = ROOT / "docs" / "reports" / "SPRINT_79_PHYSICS_MASTERY_CHECKS.json"

ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
WORD_RE = re.compile(r"[A-Za-zΔΣΦμρθλωε]+[A-Za-z0-9_]*|[\u0600-\u06FF]{2,}")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = ARABIC_DIACRITICS.sub("", text)
    return (
        text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        .replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
        .replace("ـ", "")
    )


def tokens(value: Any) -> set[str]:
    ignored = {
        "في", "من", "الى", "على", "عن", "مع", "او", "و", "ثم", "هذا", "هذه", "ذلك",
        "التي", "الذي", "عند", "كل", "بين", "درس", "وحده", "فيزياء", "استخدام", "تطبيقات",
    }
    return {t for t in WORD_RE.findall(norm(value)) if len(t) > 1 and t not in ignored}


def unique(items: Iterable[Any], key=lambda x: x) -> list[Any]:
    out: list[Any] = []
    seen: set[Any] = set()
    for item in items:
        marker = key(item)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def short(value: Any, limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


SYMBOLS: dict[str, tuple[str, str]] = {
    "v": ("السرعة", "m/s"), "vi": ("السرعة الابتدائية", "m/s"), "vf": ("السرعة النهائية", "m/s"),
    "v0": ("السرعة الابتدائية", "m/s"), "a": ("التسارع", "m/s²"), "g": ("تسارع الجاذبية", "m/s²"),
    "d": ("المسافة أو الإزاحة حسب السياق", "m"), "x": ("الموقع أو الإزاحة", "m"),
    "y": ("الموقع الرأسي", "m"), "t": ("الزمن", "s"), "f": ("القوة أو التردد حسب السياق", "N أو Hz"),
    "m": ("الكتلة", "kg"), "r": ("نصف القطر أو المسافة بين المركزين", "m"),
    "w": ("الشغل أو الوزن حسب السياق", "J أو N"), "p": ("الزخم أو القدرة حسب السياق", "kg·m/s أو W"),
    "ke": ("الطاقة الحركية", "J"), "pe": ("طاقة الوضع", "J"), "q": ("الشحنة الكهربائية", "C"),
    "i": ("شدة التيار", "A"), "vtotal": ("فرق الجهد الكلي", "V"), "req": ("المقاومة المكافئة", "Ω"),
    "c": ("سرعة الضوء", "m/s"), "h": ("ثابت بلانك أو الارتفاع حسب السياق", "J·s أو m"),
    "e": ("الطاقة أو المجال الكهربائي حسب السياق", "J أو N/C"), "b": ("المجال المغناطيسي", "T"),
    "l": ("الطول", "m"), "n": ("عدد اللفات أو عدد الجسيمات", "بلا وحدة"),
    "z": ("العدد الذري", "بلا وحدة"), "n0": ("العدد الابتدائي", "بلا وحدة"),
    "θ": ("الزاوية", "درجة أو rad"), "ω": ("السرعة الزاوية", "rad/s"),
    "α": ("التسارع الزاوي", "rad/s²"), "λ": ("الطول الموجي", "m"),
    "φ": ("الفيض", "حسب السياق"), "μ": ("معامل الاحتكاك", "بلا وحدة"),
    "ρ": ("الكثافة", "kg/m³"), "δt": ("الفترة الزمنية", "s"), "δx": ("التغير في الموقع", "m"),
    "δv": ("التغير في السرعة", "m/s"), "δe": ("التغير في الطاقة", "J"),
}

DERIVED_FORMS: list[tuple[str, list[str]]] = [
    ("v=ir", ["I = V/R", "R = V/I"]),
    ("f=ma", ["a = F/m", "m = F/a"]),
    ("p=iv", ["I = P/V", "V = P/I"]),
    ("e=pt", ["P = E/t", "t = E/P"]),
    ("v=d/t", ["d = vt", "t = d/v"]),
    ("a=δv/δt", ["Δv = aΔt", "Δt = Δv/a"]),
    ("v=δx/δt", ["Δx = vΔt", "Δt = Δx/v"]),
    ("p=mv", ["m = p/v", "v = p/m"]),
    ("ke=1/2mv", ["v = √(2KE/m)"]),
    ("c=fλ", ["f = c/λ", "λ = c/f"]),
    ("e=hf", ["f = E/h"]),
    ("λ=h/p", ["p = h/λ"]),
    ("a=z+n", ["N = A - Z", "Z = A - N"]),
]


def compact_formula(value: Any) -> str:
    return re.sub(r"[\s²^{}()_]+", "", norm(value)).replace("∆", "δ").replace("Δ", "δ")


def derived_forms(formula: str) -> list[str]:
    compact = compact_formula(formula)
    for needle, forms in DERIVED_FORMS:
        if needle in compact:
            return forms
    return []


def formula_symbols(formula: str) -> list[dict[str, str]]:
    raw = re.findall(r"Σ?[A-Za-zΔΦμρθλωε]+[0-9A-Za-z_]*", formula or "")
    out: list[dict[str, str]] = []
    for symbol in unique(raw, key=lambda x: x.lower()):
        key = norm(symbol).replace("Δ", "δ").replace("φ", "φ")
        key = key.lower()
        base = re.sub(r"[0-9_].*$", "", key)
        meaning, unit = SYMBOLS.get(key, SYMBOLS.get(base, ("رمز في العلاقة", "حسب الكمية")))
        out.append({"symbol": symbol, "meaning": meaning, "unit": unit})
    return out[:8]


def when_not_to_use(title: str, formula: str, lesson_title: str) -> str:
    hay = norm(" ".join([title, formula, lesson_title]))
    if "تسارع ثابت" in hay or "حركه بتسارع ثابت" in hay:
        return "لا تستخدمها إذا كان التسارع متغيرًا خلال الفترة المدروسة، إلا بعد تقسيم الحركة إلى فترات مناسبة."
    if "متوسط" in hay:
        return "لا تستخدم القيمة المتوسطة بدل القيمة اللحظية عندما يطلب السؤال السرعة أو التسارع عند لحظة محددة."
    if "جذب" in hay:
        return "لا تستخدم مسافة السطحين؛ المسافة في العلاقة تقاس بين مركزي الجسمين."
    if "احتكاك" in hay:
        return "لا تفترض أن الاحتكاك السكوني يساوي قيمته العظمى دائمًا؛ هو يتدرج حتى الحد الأقصى."
    if "اوم" in hay or "v=ir" in compact_formula(formula):
        return "لا تطبق قانون أوم مباشرة قبل تحديد فرق الجهد والمقاومة الصحيحة ونوع التوصيل."
    if "فاراداي" in hay or "فيض" in hay:
        return "وجود مجال مغناطيسي ثابت وحده لا يكفي؛ يلزم تغير الفيض خلال الزمن."
    if "طاقة الفوتون" in hay or "e=hf" in compact_formula(formula):
        return "لا تربط طاقة الفوتون بشدة الضوء؛ طاقة الفوتون الواحد تعتمد على التردد."
    return "لا تستخدم العلاقة قبل تحديد معنى كل رمز، توحيد الوحدات، والتأكد أن شروط المسألة توافق شروط القانون."


def base_skill_for(summary: dict[str, Any]) -> dict[str, str]:
    hay = norm(" ".join([summary.get("title", ""), summary.get("unit", ""), summary.get("core_rule", "")]))
    if any(k in hay for k in ["منحني", "رسم", "تصوير", "موقع-الزمن"]):
        return {"title": "قراءة المحاور والميل", "reason": "ستحتاج إلى التمييز بين قيمة المحور وميل المنحنى قبل تفسير الحركة."}
    if any(k in hay for k in ["متجه", "بعدين", "مقذوف", "زاويه"]):
        return {"title": "المتجهات والمركبات", "reason": "حدد الاتجاه الموجب وحلل الكمية إلى مركبات قبل تطبيق العلاقات."}
    if any(k in hay for k in ["دائره", "كهرب", "مقاوم", "تيار", "جهد"]):
        return {"title": "الوحدات ومسار الدائرة", "reason": "ميّز بين التيار والجهد والمقاومة، وحدد هل المسار مفتوح أو مغلق."}
    if any(k in hay for k in ["موجه", "ضوء", "صوت", "تداخل", "حيود"]):
        return {"title": "التردد والطول الموجي", "reason": "اربط بين التردد والطول الموجي والسرعة، وانتبه إلى الوسط الذي تنتقل فيه الموجة."}
    if any(k in hay for k in ["ذره", "كم", "نووي", "نواه"]):
        return {"title": "الرموز العلمية وحفظ الكميات", "reason": "اقرأ الرموز بدقة وحافظ على الطاقة أو الشحنة أو العددين A وZ حسب المسألة."}
    return {"title": "قراءة المعطيات والوحدات", "reason": "حوّل الوحدات وحدد المطلوب قبل اختيار القانون أو تفسير العلاقة."}


def item_score(item: dict[str, Any] | str, summary: dict[str, Any]) -> float:
    text = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
    item_tokens = tokens(text)
    title_tokens = tokens(summary.get("title"))
    concept_tokens = tokens(" ".join(summary.get("keywords", []) + [summary.get("core_rule", "")]))
    score = len(item_tokens & title_tokens) * 6 + len(item_tokens & concept_tokens) * 1.5
    # Formula overlap is highly meaningful.
    if isinstance(item, dict) and item.get("formula"):
        a = set(re.findall(r"[A-Za-zΔΣΦμρθλωε]+", str(item.get("formula"))))
        b = set(re.findall(r"[A-Za-zΔΣΦμρθλωε]+", str(summary.get("core_rule", ""))))
        score += len(a & b) * 2
    return score


def find_summary_from_label(label: str, summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    nlabel = norm(re.sub(r"^\s*\d+[-–]\d+\s*", "", label or ""))
    for summary in summaries:
        nt = norm(summary.get("title"))
        if nt and (nt in nlabel or nlabel in nt):
            return summary
    return None




# Route rich unit-level cards to the exact lesson when the source label is
# unambiguous. This prevents sibling lessons in the same unit from receiving
# a scientifically related but pedagogically misplaced formula or example.
ROUTE_HINTS: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("مقذوف", "قذف", "السرعه العموديه", "السرعه الافقيه"), ("حركه المقذوف",)),
    (("مركزي", "دائري", "منعطف"), ("الحركه الدائريه",)),
    (("نسبيه", "اطار مرجعي", "قطار"), ("السرعه المتجهه النسبيه",)),
    (("هوك", "نابض", "بندول", "زمن دوري", "حركه دوريه"), ("الحركه الدوريه",)),
    (("سرعه الموجه", "مستعرضه", "طوليه", "طول موجي"), ("خصايص الموجات",)),
    (("تداخل", "تراكب", "انكسار موجه", "حيود"), ("سلوك الموجات", "التداخل")),
    (("مجال حول سلك", "اتجاه المجال حول سلك", "مغناطيس دائم", "خطوط المجال"), ("المغانط الدايمه والموقته",)),
    (("قوه مغناطيسيه", "قوه على شحنه", "قوه على سلك", "محرك كهربايي"), ("القوي الناتجه عن المجالات المغناطيسيه",)),
    (("فاراداي", "لنز", "تغير الفيض", "تحريك مغناطيس", "مساحه ملف"), ("التيار الناتج عن تغير المجالات المغناطيسيه",)),
    (("محول", "رفع الجهد", "خفض الجهد", "موصل متحرك", "مولد كهربايي"), ("تغير المجال يولد قوه دافعه حثيه",)),
    (("عدد الكتله", "عدد النيوترونات", "طاقه الربط"), ("النواه",)),
    (("نصف العمر", "الفا", "بيتا", "جاما", "اضمحلال"), ("الاضمحلال النووي والتفاعلات النوويه",)),
    (("كوارك", "لبتون", "النموذج المعياري", "وحدات بناء"), ("وحدات بناء الماده",)),
]

def route_target(payload: dict[str, Any], lessons: list[dict[str, Any]]) -> dict[str, Any] | None:
    hay = norm(json.dumps(payload, ensure_ascii=False))
    for needles, targets in ROUTE_HINTS:
        if not any(norm(needle) in hay for needle in needles):
            continue
        for target in targets:
            matches = [lesson for lesson in lessons if norm(target) in norm(lesson.get("title", ""))]
            if matches:
                return matches[0]
    return None


def build_unit_assignments(
    summaries: list[dict[str, Any]], enrichment: dict[str, list[dict[str, Any]]]
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    assignments: dict[str, dict[str, list[dict[str, Any]]]] = {}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        groups[(summary["stage"], summary["unit"])].append(summary)
    for values in groups.values():
        values.sort(key=lambda s: (s.get("order", 0), s.get("title", "")))

    for (stage, unit), lesson_summaries in groups.items():
        rich_unit = next((u for u in enrichment.get(stage, []) if norm(u.get("unit")) == norm(unit)), {})
        for summary in lesson_summaries:
            assignments[summary["summary_id"]] = defaultdict(list)

        # Explicit lesson code mapping from source definitions.
        codes = unique(
            [str(d.get("lesson", "")).strip() for d in rich_unit.get("definitions", []) if d.get("lesson")]
            + [str(g.get("lesson", "")).split()[0] for g in rich_unit.get("tahsili_question_groups", []) if g.get("lesson")]
        )
        codes.sort(key=lambda x: tuple(int(n) for n in re.findall(r"\d+", x)) or (999,))
        code_map = {code: lesson_summaries[i] for i, code in enumerate(codes[: len(lesson_summaries)])}

        for definition in rich_unit.get("definitions", []):
            target = code_map.get(str(definition.get("lesson", "")).strip())
            if not target:
                target = max(lesson_summaries, key=lambda s: item_score(definition, s))
            assignments[target["summary_id"]]["definitions"].append(deepcopy(definition))

        for group in rich_unit.get("tahsili_question_groups", []) or []:
            target = find_summary_from_label(group.get("lesson", ""), lesson_summaries)
            if not target:
                target = max(lesson_summaries, key=lambda s: item_score(group, s))
            assignments[target["summary_id"]]["questions"].extend(deepcopy(group.get("questions", [])))

        # Ungrouped lists are assigned only when lesson-specific vocabulary supports
        # the match. Ambiguous unit-level items are intentionally skipped rather
        # than attached to the wrong lesson.
        def enriched_score(payload: dict[str, Any], lesson: dict[str, Any]) -> float:
            score = item_score(payload, lesson)
            definition_terms = " ".join(
                f"{d.get('term', '')} {d.get('text', '')}"
                for d in assignments[lesson["summary_id"]].get("definitions", [])
            )
            score += len(tokens(json.dumps(payload, ensure_ascii=False)) & tokens(definition_terms)) * 3
            return score

        for source_key, target_key in (
            ("formula_cards", "formulas"), ("worked_examples", "examples"),
            ("relationship_cards", "relationships"), ("dont_confuse", "confusions"),
            ("tahsili_questions", "questions"),
        ):
            for item in rich_unit.get(source_key, []) or []:
                routed = route_target(item, lesson_summaries)
                if routed is not None:
                    assignments[routed["summary_id"]][target_key].append(deepcopy(item))
                    continue
                ranked = sorted(lesson_summaries, key=lambda s: enriched_score(item, s), reverse=True)
                best = ranked[0]
                best_score = enriched_score(item, best)
                if best_score <= 0:
                    continue
                assignments[best["summary_id"]][target_key].append(deepcopy(item))

        # Unit memory points are shared only as supporting recap, not as lesson definitions.
        for summary in lesson_summaries:
            assignments[summary["summary_id"]]["unit_keep"] = deepcopy(rich_unit.get("keep_box", []))
            assignments[summary["summary_id"]]["source"] = [{
                "book": rich_unit.get("source_book", summary.get("stage")),
                "pages": rich_unit.get("source_pages", summary.get("coverage_status", {}).get("source_pages", "")),
            }]
    return assignments


def option_set(correct: str, distractors: Iterable[str], limit: int = 4) -> tuple[list[str], int]:
    values = unique([short(correct, 165)] + [short(x, 165) for x in distractors if str(x).strip()])[:limit]
    while len(values) < limit:
        values.append(["لا توجد علاقة بين الكميات", "يمكن تجاهل الوحدات دائمًا", "يكفي حفظ الناتج دون فهم"][(len(values) - 1) % 3])
    # Deterministic rotation keeps the correct option from always being first.
    shift = sum(ord(ch) for ch in correct) % len(values)
    values = values[shift:] + values[:shift]
    return values, values.index(short(correct, 165))


def as_practice(q: dict[str, Any], source: str, difficulty: str | None = None) -> dict[str, Any] | None:
    prompt = q.get("q") or q.get("question")
    options = q.get("options") or q.get("choices")
    answer = q.get("answer")
    if isinstance(answer, str) and options:
        try:
            answer = options.index(answer)
        except ValueError:
            answer = q.get("correct", 0)
    if answer is None:
        answer = q.get("correct")
    if not prompt or not isinstance(options, list) or not options or not isinstance(answer, int) or not (0 <= answer < len(options)):
        return None
    explanation = q.get("explain")
    if not explanation and isinstance(q.get("explanation"), dict):
        explanation = q["explanation"].get("summary") or " ".join(q["explanation"].get("steps", []))
    explanation = explanation or q.get("editorial_explain") or "راجع الفكرة والقانون ثم قارن كل اختيار بالمعطيات."
    return {
        "question": str(prompt), "options": [str(x) for x in options], "correct_index": answer,
        "explanation": str(explanation), "difficulty": difficulty or q.get("difficulty") or "متوسط",
        "source": source, "question_id": q.get("id", ""),
    }


def make_generated_questions(summary: dict[str, Any], peer_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concepts = summary.get("concept_map", [])
    peers = [p for p in peer_summaries if p["summary_id"] != summary["summary_id"]]
    generated: list[dict[str, Any]] = []
    if concepts:
        c = concepts[0]
        distractors = [x.get("description", "") for x in concepts[1:]] + [p.get("simple_idea", "") for p in peers[:2]]
        opts, idx = option_set(c.get("description", ""), distractors)
        generated.append({
            "question": f"أي وصف يعبّر بدقة عن «{c.get('title', 'المفهوم')}»؟", "options": opts,
            "correct_index": idx, "explanation": f"{c.get('title')}: {c.get('description')}",
            "difficulty": "سهل", "source": "مولد من التعريف المعتمد", "question_id": "",
        })
    peer_rules = [p.get("core_rule", "") for p in peers if p.get("core_rule")]
    opts, idx = option_set(summary.get("core_rule", ""), peer_rules[:4])
    generated.append({
        "question": f"ما القاعدة أو العلاقة الأساسية الأقرب إلى درس «{summary.get('title')}»؟", "options": opts,
        "correct_index": idx, "explanation": summary.get("core_rule", ""),
        "difficulty": "متوسط", "source": "مولد من القاعدة المعتمدة", "question_id": "",
    })
    tip = summary.get("suhail_tip") or summary.get("simple_back") or "حدد المعطيات والمطلوب والوحدات."
    opts, idx = option_set(tip, ["استخدم أول قانون تتذكره دون قراءة السؤال", "أهمل اتجاه الكميات المتجهة", "اكتب الناتج من دون وحدة"])
    generated.append({
        "question": f"أي إجراء يساعدك أكثر على تجنب الفخ في درس «{summary.get('title')}»؟", "options": opts,
        "correct_index": idx, "explanation": tip,
        "difficulty": "متوسط", "source": "مولد من تلميح سهيل", "question_id": "",
    })
    chain = [c.get("title", "") for c in concepts if c.get("title")]
    if len(chain) >= 2:
        correct = " ← ".join(chain)
        reversed_chain = " ← ".join(reversed(chain))
        shuffled = " ← ".join(chain[1:] + chain[:1])
        opts, idx = option_set(correct, [reversed_chain, shuffled, "لا توجد علاقة بين مفاهيم الدرس"])
        generated.append({
            "question": f"أي تسلسل يمثّل خريطة الفهم في درس «{summary.get('title')}»؟", "options": opts,
            "correct_index": idx, "explanation": f"تسلسل الفهم المعتمد: {correct}",
            "difficulty": "متوسط", "source": "مولد من خريطة المفاهيم", "question_id": "",
        })
    example_text = str((summary.get("example") or {}).get("text") or summary.get("simple_idea") or "")
    if example_text:
        correct = summary.get("title", "")
        distractors = [p.get("title", "") for p in peers[:3]]
        opts, idx = option_set(correct, distractors)
        generated.append({
            "question": f"الموقف الآتي يرتبط بأي درس؟ «{short(example_text, 120)}»", "options": opts,
            "correct_index": idx, "explanation": f"الموقف يطبّق الفكرة الأساسية في درس {correct}: {summary.get('simple_idea', '')}",
            "difficulty": "صعب", "source": "مولد من المثال المعتمد", "question_id": "",
        })
    return unique(generated, key=lambda x: norm(x["question"]))


def build_formula_cards(summary: dict[str, Any], assigned: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    raw = list(assigned.get("formulas", []))
    raw.extend(
        {"title": b.get("title") or "العلاقة الأساسية", "formula": b.get("content"), "use": summary.get("essence_buttons", {}).get("formula", "")}
        for b in summary.get("knowledge_blocks", []) if b.get("type") == "rule"
    )
    if not raw:
        raw = [{"title": "القاعدة الأساسية", "formula": summary.get("core_rule", ""), "use": "استخدمها لتفسير العلاقة الأساسية في الدرس."}]
    cards: list[dict[str, Any]] = []
    for item in unique(raw, key=lambda x: compact_formula(str(x.get("formula", ""))) or norm(str(x.get("title", "")))):
        formula = str(item.get("formula") or summary.get("core_rule") or "").strip()
        if not formula:
            continue
        use = str(item.get("use") or summary.get("essence_buttons", {}).get("formula") or "حدد المعطيات والمطلوب ثم طبّق العلاقة.")
        cards.append({
            "title": str(item.get("title") or "العلاقة الأساسية"),
            "formula": formula,
            "meaning": use,
            "symbols": formula_symbols(formula),
            "when_to_use": use,
            "when_not_to_use": when_not_to_use(str(item.get("title", "")), formula, summary.get("title", "")),
            "derived_forms": derived_forms(formula),
            "tip": summary.get("suhail_tip") or "اقرأ معنى الرمز ووحدته قبل التعويض.",
            "common_error": summary.get("essence_buttons", {}).get("trap") or summary.get("common_mistakes", [""])[0],
            "source_page": item.get("page", ""),
        })
    return cards[:4]


def build_practice(
    summary: dict[str, Any], assigned: dict[str, list[dict[str, Any]]], linked: list[dict[str, Any]],
    peers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    check = summary.get("check_question") or {}
    if check:
        item = as_practice({
            "q": check.get("question"), "options": check.get("options"), "answer": check.get("correct_index"),
            "explain": check.get("explanation"), "difficulty": "سهل",
        }, "سؤال تثبيت الملخص", "سهل")
        if item:
            candidates.append(item)
    for q in assigned.get("questions", []):
        item = as_practice(q, "أمثلة التحصيلي في الكتاب")
        if item:
            candidates.append(item)
    # Exact external bank links only; medium/hard first because these add the most teaching value.
    for q in sorted(linked, key=lambda x: {"صعب": 0, "متوسط": 1, "سهل": 2}.get(x.get("difficulty"), 3)):
        item = as_practice(q, "بنك الأسئلة المرتبط")
        if item:
            candidates.append(item)
    candidates.extend(make_generated_questions(summary, peers))
    result = unique(candidates, key=lambda x: norm(x["question"]))
    # Guarantee five valid items and a sensible difficulty ladder.
    generated = make_generated_questions(summary, peers)
    for base in generated:
        if len(result) >= 5:
            break
        if norm(base["question"]) not in {norm(x["question"]) for x in result}:
            result.append(deepcopy(base))
    while len(result) < 5:
        n = len(result) + 1
        correct = summary.get("simple_idea") or summary.get("core_rule")
        opts, idx = option_set(correct, [p.get("simple_idea", "") for p in peers[:3]])
        result.append({
            "question": f"تطبيق {n}: أي تفسير يطابق درس «{summary.get('title')}»؟",
            "options": opts, "correct_index": idx, "explanation": correct,
            "difficulty": "متوسط", "source": "تثبيت مولد من الفكرة الأساسية", "question_id": "",
        })
    result = unique(result, key=lambda x: norm(x["question"]))[:5]
    wanted = ["سهل", "متوسط", "متوسط", "متوسط", "صعب"]
    for i, item in enumerate(result):
        if not item.get("difficulty"):
            item["difficulty"] = wanted[i]
        if i == len(result) - 1:
            item["difficulty"] = "صعب"
    return result


def build_examples(summary: dict[str, Any], assigned: dict[str, list[dict[str, Any]]], practice: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    base_text = str((summary.get("example") or {}).get("text") or "")
    if base_text:
        examples.append({
            "level": "تأسيسي", "title": "افهم الموقف قبل الحساب", "problem": base_text,
            "given": [short(x.get("title")) for x in summary.get("concept_map", [])[:2]],
            "required": "تحديد الفكرة التي يوضحها الموقف.",
            "why_this_method": "لأن البداية الصحيحة هي ربط الموقف بالمفهوم، ثم اختيار العلاقة عند الحاجة.",
            "steps": [
                f"حدد المفهوم الأساسي: {summary.get('concept_map', [{}])[0].get('title', summary.get('title'))}.",
                f"اربطه بالقاعدة: {summary.get('core_rule', '')}",
                "تحقق أن الاتجاه والوحدة وشروط العلاقة متوافقة مع الموقف.",
            ],
            "answer": summary.get("simple_idea", ""), "check": "هل تستطيع شرح النتيجة بالكلمات قبل كتابة القانون؟",
            "source_page": "",
        })
    for item in assigned.get("examples", [])[:2]:
        steps = [str(s) for s in item.get("steps", []) if str(s).strip()]
        if not steps:
            continue
        examples.append({
            "level": "متوسط" if len(examples) == 1 else "متقدم", "title": item.get("title", "مثال محلول"),
            "problem": item.get("title", "طبّق الفكرة على موقف جديد."), "given": [],
            "required": "الوصول إلى النتيجة مع تبرير اختيار الطريقة.",
            "why_this_method": f"نستخدم الفكرة والقانون المرتبطين بدرس {summary.get('title')} بدل التعويض العشوائي.",
            "steps": steps, "answer": steps[-1],
            "check": "راجع الوحدة والإشارة، ثم اسأل هل النتيجة منطقية مقارنة بالمعطيات؟",
            "source_page": item.get("page", ""),
        })
    if len(examples) < 3 and practice:
        q = next((x for x in practice if x.get("difficulty") in {"صعب", "متوسط"}), practice[-1])
        examples.append({
            "level": "متقدم" if len(examples) >= 2 else "متوسط", "title": "حل سؤال تحصيلي خطوة بخطوة",
            "problem": q["question"], "given": ["اقرأ المعطيات والكلمات المفتاحية في السؤال"],
            "required": "اختيار الإجابة الصحيحة ورفض المشتتات القريبة.",
            "why_this_method": q["explanation"],
            "steps": [
                f"حدّد الدرس المطلوب: {summary.get('title')}.",
                f"استدعِ القاعدة المناسبة: {summary.get('core_rule')}.",
                "قارن كل اختيار بشرط القانون والوحدة والاتجاه.",
                f"الإجابة الصحيحة: {q['options'][q['correct_index']]}",
            ],
            "answer": q["options"][q["correct_index"]], "check": q["explanation"], "source_page": "",
        })
    # A correction example is pedagogically safer than duplicating a weak numerical example.
    if len(examples) < 3:
        trap = summary.get("essence_buttons", {}).get("trap") or summary.get("common_mistakes", ["انتبه لشروط القانون."])[0]
        examples.append({
            "level": "متقدم", "title": "صحح الحل الخاطئ", "problem": trap, "given": ["حل يحتوي على خطأ مفاهيمي"],
            "required": "اكتشاف موضع الخطأ وتصحيحه.", "why_this_method": "التحصيلي يختبر الفروق الدقيقة والمشتتات القريبة.",
            "steps": ["حدد العبارة غير الصحيحة.", "ارجع إلى معنى الكميات وشروط القانون.", "اكتب التصحيح بجملة واحدة.", f"طبّق القاعدة: {summary.get('core_rule')}."],
            "answer": summary.get("suhail_tip", "راجع معنى الرموز والوحدات."),
            "check": "هل يختفي الفخ إذا تغيرت الإشارة أو المرجع أو الوحدة؟", "source_page": "",
        })
    return examples[:3]


def build_dont_confuse(summary: dict[str, Any], assigned: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for item in assigned.get("confusions", []):
        items.append({"title": item.get("title", "لا تخلط"), "explanation": item.get("text", "")})
    for row in summary.get("comparison", []) or []:
        items.append({
            "title": f"ميّز «{row.get('case', 'المفهوم')}»",
            "explanation": " — ".join(x for x in [row.get("effect", ""), row.get("example", "")] if x),
        })
    if len(items) < 2:
        items.append({"title": "لا تخلط بين حفظ القانون وفهمه", "explanation": summary.get("essence_buttons", {}).get("trap", "")})
    return unique(items, key=lambda x: norm(x["title"] + x["explanation"]))[:4]


def build_exam_patterns(summary: dict[str, Any], formulas: list[dict[str, Any]]) -> list[dict[str, str]]:
    title = summary.get("title", "الدرس")
    patterns = [
        {"type": "تعريف ومفهوم", "recognize": f"يطلب معنى مصطلح أساسي من {title} أو يصفه بموقف.", "strategy": "طابق الوصف مع التعريف، ولا تعتمد على كلمة واحدة فقط."},
        {"type": "علاقة وسبب", "recognize": "يسأل ماذا يزداد أو ينقص أو ما سبب الظاهرة.", "strategy": f"ابدأ بالعلاقة: {short(summary.get('core_rule'), 110)}"},
        {"type": "فخ مفاهيمي", "recognize": "تكون الخيارات متقاربة لكن أحدها يخلط بين كميتين أو يهمل شرطًا.", "strategy": short(summary.get("essence_buttons", {}).get("trap", "راجع الاتجاه والوحدة وشروط القانون."), 150)},
    ]
    hay = norm(" ".join([summary.get("title", ""), summary.get("unit", ""), summary.get("simple_idea", "")]))
    if any(k in hay for k in ["منحني", "رسم", "موجه", "طيف", "صور"]):
        patterns.append({"type": "رسم أو تمثيل", "recognize": "يعرض منحنى أو خطوطًا أو صورة متتابعة ويطلب تفسيرها.", "strategy": "سمِّ المحاور أولًا، ثم اقرأ الميل أو التباعد أو الاتجاه بدل شكل الرسم وحده."})
    elif formulas:
        patterns.append({"type": "مسألة حسابية", "recognize": "يعطي أرقامًا ووحدات ويطلب كمية مجهولة.", "strategy": "اكتب المعطيات، وحّد الوحدات، اختر علاقة لا تحتوي مجهولًا إضافيًا، ثم تحقق من منطق الناتج."})
    else:
        patterns.append({"type": "مقارنة", "recognize": "يقارن حالتين تغير فيهما عامل واحد.", "strategy": "ثبّت بقية العوامل وحدد هل العلاقة طردية أم عكسية أم وصفية."})
    return patterns


def build_blocks(summary: dict[str, Any], learning: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = deepcopy(summary.get("knowledge_blocks", []))
    prefix = re.match(r"PHY-\d+", blocks[0]["id"] if blocks else "")
    prefix_value = prefix.group(0) if prefix else f"PHY-{int(summary.get('order', 0)):03d}"
    extra: list[tuple[str, str, str, bool]] = []
    for i, item in enumerate(learning["prerequisites"], 1):
        extra.append((f"PRE-{i:02d}", "prerequisite", item["title"], False))
    for i, item in enumerate(learning["formula_cards"], 1):
        extra.append((f"FORMULA-{i:02d}", "formula", f"{item['title']}: {item['formula']}", True))
    for i, item in enumerate(learning["worked_examples"], 1):
        extra.append((f"WORKED-{i:02d}", "worked_example", f"{item['title']}: {item['answer']}", False))
    extra.append(("MASTERY-01", "mastery", learning["takeaway"]["understanding_signal"], True))
    existing_ids = {b.get("id") for b in blocks}
    order = max([int(b.get("order", 0)) for b in blocks] + [0]) + 10
    for suffix, kind, content, is_core in extra:
        block_id = f"{prefix_value}-{suffix}"
        if block_id in existing_ids:
            continue
        title = {
            "prerequisite": "قبل أن تبدأ", "formula": "القانون بمعناه",
            "worked_example": "مثال محلول", "mastery": "علامة الإتقان",
        }[kind]
        search = norm(" ".join([title, content, summary.get("title", ""), summary.get("unit", "")]))
        blocks.append({
            "id": block_id, "summary_id": summary["summary_id"], "subject": "فيزياء",
            "stage": summary["stage"], "unit": summary["unit"], "lesson": summary["title"],
            "type": kind, "title": title, "content": content,
            "keywords": unique(summary.get("keywords", []) + [title, kind]),
            "order": order, "is_core": is_core, "search_text": search,
        })
        order += 10
    return blocks


def main() -> None:
    summaries: list[dict[str, Any]] = load(SUMMARIES_SOURCE_PATH if SUMMARIES_SOURCE_PATH.exists() else SUMMARIES_PATH)
    questions: list[dict[str, Any]] = load(QUESTIONS_PATH)
    enrichment: dict[str, list[dict[str, Any]]] = load(UNIT_ENRICHMENT_PATH)
    assignments = build_unit_assignments(summaries, enrichment)

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        groups[(summary["stage"], summary["unit"])].append(summary)
    for group in groups.values():
        group.sort(key=lambda x: (x.get("order", 0), x.get("title", "")))

    linked_by_summary: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in questions:
        if q.get("subject") == "فيزياء" and q.get("summary_id"):
            linked_by_summary[str(q["summary_id"])].append(q)

    upgraded: list[dict[str, Any]] = []
    all_blocks: list[dict[str, Any]] = []
    summaries_map: list[dict[str, Any]] = []

    for summary in summaries:
        item = deepcopy(summary)
        sid = item["summary_id"]
        peers = groups[(item["stage"], item["unit"])]
        index = peers.index(summary)
        assigned = assignments.get(sid, defaultdict(list))
        previous = peers[index - 1] if index > 0 else None
        next_lesson = peers[index + 1] if index + 1 < len(peers) else None

        prerequisites = []
        if previous:
            prerequisites.append({
                "title": previous["title"],
                "reason": f"هذا الدرس يبني على فكرة «{previous.get('simple_idea', previous['title'])}»؛ راجعها سريعًا إذا كانت غير واضحة.",
                "summary_id": previous["summary_id"],
            })
        else:
            prerequisites.append({
                "title": "أساسيات الوحدة", "reason": f"ابدأ بفهم معنى {item.get('concept_map', [{}])[0].get('title', item['title'])} قبل حفظ أي علاقة.",
                "summary_id": "",
            })
        prerequisites.append({**base_skill_for(item), "summary_id": ""})

        definitions = [
            {"term": c.get("title", ""), "meaning": c.get("description", ""), "example": "", "source_page": ""}
            for c in item.get("concept_map", []) if c.get("title")
        ]
        definitions.extend({
            "term": d.get("term", ""), "meaning": d.get("text", ""),
            "example": "", "source_page": d.get("page", ""),
        } for d in assigned.get("definitions", []))
        definitions = unique(definitions, key=lambda x: norm(x["term"]))[:9]

        formulas = build_formula_cards(item, assigned)
        practice = build_practice(item, assigned, linked_by_summary.get(sid, []), peers)
        examples = build_examples(item, assigned, practice)
        confusions = build_dont_confuse(item, assigned)
        traps = unique(
            [str(x) for x in item.get("common_mistakes", []) if str(x).strip()]
            + [item.get("essence_buttons", {}).get("trap", "")]
            + [x.get("explanation", "") for x in confusions[:2]],
            key=norm,
        )[:5]
        relationships = unique(
            [
                {"title": r.get("title", "الربط المفاهيمي"), "explanation": r.get("text", "")}
                for r in assigned.get("relationships", [])
            ]
            + [{"title": "تسلسل الفهم", "explanation": " ← ".join(c.get("title", "") for c in item.get("concept_map", []))}],
            key=lambda x: norm(x["title"] + x["explanation"]),
        )[:4]
        diagnostic = as_practice({
            "q": item.get("check_question", {}).get("question"),
            "options": item.get("check_question", {}).get("options"),
            "answer": item.get("check_question", {}).get("correct_index"),
            "explain": item.get("check_question", {}).get("explanation"),
        }, "تشخيص قبل الدرس", "تشخيصي") or practice[0]

        learning = {
            "template_version": "2.0.79",
            "lesson_number": index + 1,
            "lesson_count_in_unit": len(peers),
            "estimated_minutes": min(28, 12 + len(formulas) * 2 + len(examples)),
            "prerequisites": prerequisites,
            "diagnostic_question": diagnostic,
            "from_zero": [
                item.get("simple_idea", ""),
                " ثم ".join(
                    f"{c.get('title')}: {c.get('description')}" for c in item.get("concept_map", [])[:3]
                ),
                relationships[0]["explanation"] if relationships else item.get("links_back", ""),
            ],
            "concept_chain": [c.get("title", "") for c in item.get("concept_map", []) if c.get("title")],
            "relationships": relationships,
            "definitions": definitions,
            "formula_cards": formulas,
            "worked_examples": examples,
            "dont_confuse": confusions,
            "common_traps": traps,
            "exam_patterns": build_exam_patterns(item, formulas),
            "practice_questions": practice,
            "takeaway": {
                "main_idea": item.get("simple_idea", ""),
                "main_rule": item.get("core_rule", ""),
                "main_trap": item.get("essence_buttons", {}).get("trap", ""),
                "understanding_signal": f"تكون قد فهمت درس {item['title']} عندما تستطيع شرح العلاقة بالكلمات، اختيار القانون المناسب، وحل 4 من 5 أسئلة دون تلميح.",
            },
            "mastery": {
                "minimum_score_percent": 80,
                "required_correct": 4,
                "question_count": 5,
                "requires_definition_review": True,
                "requires_formula_review": bool(formulas),
                "retry_wrong_only": True,
                "status_storage_key": f"suhail79_mastery::{sid}",
            },
            "navigation": {
                "previous_summary_id": previous["summary_id"] if previous else "",
                "next_summary_id": next_lesson["summary_id"] if next_lesson else "",
            },
            "source": assigned.get("source", []),
            "external_linked_question_count": len(linked_by_summary.get(sid, [])),
            "internal_practice_question_count": len(practice),
        }
        item["learning_path_v2"] = learning
        item["definitions"] = definitions
        item["formula_cards"] = formulas
        item["worked_examples"] = examples
        item["dont_confuse"] = confusions
        item["exam_patterns"] = learning["exam_patterns"]
        item["practice_questions"] = practice
        item["prerequisites"] = prerequisites
        item["mastery_check"] = learning["mastery"]
        item["scientific_links"] = [r["explanation"] for r in relationships]
        item["simple_back"] = prerequisites[-1]["reason"]
        item["linked_question_count"] = len(linked_by_summary.get(sid, []))
        item["internal_practice_count"] = len(practice)
        item["content_status"] = "physics_mastery_template_v2_internal_qa"
        item.setdefault("coverage_status", {})["sprint_79"] = "mastery_template_complete"
        item["coverage_status"]["needs_final_human_review"] = True
        item["full_content"] = {
            **(item.get("full_content") or {}),
            "prerequisites": prerequisites,
            "definitions": [f"{d['term']}: {d['meaning']}" for d in definitions],
            "formulas": [f"{f['title']}: {f['formula']}" for f in formulas],
            "examples": [e["problem"] for e in examples],
            "dont_confuse": confusions,
            "practice_questions": practice,
        }
        item["knowledge_blocks"] = build_blocks(item, learning)
        item["knowledge_block_count"] = len(item["knowledge_blocks"])
        upgraded.append(item)
        all_blocks.extend(item["knowledge_blocks"])
        summaries_map.append({
            "summary_id": sid, "stage": item["stage"], "unit": item["unit"], "title": item["title"],
            "block_ids": [b["id"] for b in item["knowledge_blocks"]],
            "linked_question_count": item["linked_question_count"],
            "internal_practice_count": item["internal_practice_count"],
            "template_version": "2.0.79",
        })

    dump(SUMMARIES_PATH, upgraded)
    dump(KNOWLEDGE_MAP_PATH, {
        "version": "79.0.0", "subject": "فيزياء", "summary_count": len(upgraded),
        "block_count": len(all_blocks), "template_version": "2.0.79",
        "summaries": summaries_map, "blocks": all_blocks,
    })
    dump(TEMPLATE_PATH, {
        "version": "2.0.79", "name": "قالب درس الفيزياء للإتقان",
        "required_sections": [
            "prerequisites", "diagnostic_question", "from_zero", "concept_chain", "relationships",
            "definitions", "formula_cards", "worked_examples", "dont_confuse", "common_traps",
            "exam_patterns", "practice_questions", "takeaway", "mastery",
        ],
        "minimums": {
            "prerequisites": 2, "definitions": 3, "formula_cards": 1, "worked_examples": 3,
            "dont_confuse": 2, "common_traps": 2, "exam_patterns": 4, "practice_questions": 5,
            "mastery_percent": 80,
        },
        "future_subject_adapters": {
            "رياضيات": "أنماط الحل والتحقق والاختصار",
            "كيمياء": "المستوى الجسيمي والمعادلات والتجارب",
            "الأحياء وعلم البيئة": "العمليات والتسلسل والخرائط والمقارنات",
        },
    })

    checks = {
        "release": "Sprint 79", "summary_count": len(upgraded),
        "stage_counts": dict(Counter(x["stage"] for x in upgraded)),
        "knowledge_block_count": len(all_blocks),
        "internal_practice_question_count": sum(len(x["practice_questions"]) for x in upgraded),
        "external_physics_question_count": sum(1 for q in questions if q.get("subject") == "فيزياء"),
        "lessons_with_exact_external_links": sum(1 for x in upgraded if x["linked_question_count"] > 0),
        "lessons_without_guessed_external_links": sum(1 for x in upgraded if x["linked_question_count"] == 0),
        "minimums": {
            "prerequisites": min(len(x["prerequisites"]) for x in upgraded),
            "definitions": min(len(x["definitions"]) for x in upgraded),
            "formula_cards": min(len(x["formula_cards"]) for x in upgraded),
            "worked_examples": min(len(x["worked_examples"]) for x in upgraded),
            "dont_confuse": min(len(x["dont_confuse"]) for x in upgraded),
            "exam_patterns": min(len(x["exam_patterns"]) for x in upgraded),
            "practice_questions": min(len(x["practice_questions"]) for x in upgraded),
        },
        "valid_practice_answers": all(
            all(0 <= q["correct_index"] < len(q["options"]) and bool(q["explanation"].strip()) for q in x["practice_questions"])
            for x in upgraded
        ),
        "unique_summary_ids": len({x["summary_id"] for x in upgraded}) == len(upgraded),
        "source_policy": "Exact external links retained; no guessed links were created for uncovered lessons.",
        "editorial_note": "Structure and internal QA complete. Public release still requires a physics subject-matter review of all lesson wording and calculations.",
    }
    dump(REPORT_PATH, checks)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
