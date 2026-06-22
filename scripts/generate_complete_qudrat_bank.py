#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / 'data' / 'questions.json'
ASSET_DIR = ROOT / 'assets' / 'questions' / 'generated65'
REPORT_PATH = ROOT / 'docs' / 'reports' / 'SPRINT_65_COMPLETE_BANK_REPORT.json'
RNG = random.Random(650065)
TARGET_QUANT = 1500
TARGET_VERBAL = 1500

SOURCE_DOCS = [
    'تجميعات كمي 2026611.pdf', 'تجميعات كمي 2026613.pdf',
    'تجميعات كمي 2026615 (1).pdf', 'تجميعات لفظي 2026613.pdf',
    'تجميعات لفظي يوم الأحد 2026614.pdf', 'تجميعات لفظي 2026615 (1).pdf',
    'تجميع مظلة القسم الكمي.pdf', 'المنصف ١٥٠٠ سؤال.pdf',
    'إصدارات المفكر ٢١٥٠ سؤال من الصيغ الجديدة.pdf', 'تجميع مصباح لفظي.pdf',
    'بنك أسئلة اللفظي.pdf', 'الإصدار الثاني تجميع الحوت.pdf',
    'المفردة الشاذة من الورقي أكاديمية الحوت.pdf',
    'قوانين السرعة.pdf', 'الكسور الاعتيادية.pdf', 'قابلية القسمة.pdf',
    'الجذور.pdf', 'الاعداد العشرية.pdf',
]

# ---------- Common helpers ----------

def norm_text(s: str) -> str:
    s = str(s or '').strip().lower()
    s = re.sub(r'[\u064b-\u065f\u0670]', '', s)
    s = s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')
    s = re.sub(r'\s+', ' ', s)
    return s


def fmt_num(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f'{value.numerator}/{value.denominator}'
    if isinstance(value, int):
        return str(value)
    x = round(float(value), 4)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f'{x:.4f}'.rstrip('0').rstrip('.')


def unique_choices(correct: str, distractors: list[str]) -> list[str]:
    out = []
    for d in distractors:
        d = str(d)
        if d != str(correct) and d not in out:
            out.append(d)
        if len(out) == 3:
            break
    seed = 1
    while len(out) < 3:
        d = f'{correct} + {seed}'
        if d not in out and d != str(correct):
            out.append(d)
        seed += 1
    return out[:3]


def normalize_units(correct: str, distractors: list[str]) -> list[str]:
    m = re.fullmatch(r'(-?\d+(?:\.\d+)?(?:/\d+)?)\s+(.+)', str(correct).strip())
    if not m:
        return [str(x) for x in distractors]
    suffix = m.group(2).strip()
    markers = ('سم', 'متر', 'كم', 'ساعة', 'يوم', 'ريال', 'لتر', 'درجة', 'طالب', 'عامل', 'قطعة', 'سنة')
    if not any(k in suffix for k in markers):
        return [str(x) for x in distractors]
    out = []
    for x in distractors:
        t = str(x).strip()
        if re.fullmatch(r'-?\d+(?:\.\d+)?(?:/\d+)?', t):
            t = f'{t} {suffix}'
        out.append(t)
    return out


def difficulty_mode(difficulty: str, *, image: str = '', close_notes: dict[str, str] | None = None, force: str = '') -> str:
    if force:
        return force
    if close_notes:
        return 'full'
    if image:
        return 'brief' if difficulty == 'سهل' else 'full'
    if difficulty == 'سهل':
        return 'none'
    return 'full'


class Bank:
    def __init__(self, seed_questions: list[dict]):
        self.questions: list[dict] = []
        self.seen = set()
        self.id_counts = Counter()
        for q in seed_questions:
            self.add_existing(q)

    def add_existing(self, q: dict) -> None:
        q = dict(q)
        q.pop('test_format', None)
        q.pop('delivery_mode', None)
        q['bank'] = 'قدرات موحد'
        q['source_status'] = q.get('source_status') or 'original_transformation'
        q['rights_status'] = q.get('rights_status') or 'original'
        q['editorial_status'] = q.get('editorial_status') or 'qa_passed_internal'
        q['release_eligible'] = bool(q.get('release_eligible', True))
        # Correct literal references to source numbering in illustrated questions.
        if q.get('image') and re.search(r'(?:المستطيل|الشكل المركب) رقم\s*\d+', q.get('question', '')):
            if 'المستطيل' in q['question']:
                q['question'] = 'ما مساحة المستطيل الموضح في الشكل؟'
                q['image_alt'] = 'مستطيل موضح عليه الطول والعرض'
            else:
                q['question'] = 'ما مساحة الجزء المتبقي في الشكل المركب الموضح؟'
                q['image_alt'] = 'شكل مركب بأبعاد موضحة'
        q.setdefault('image_alt', q.get('image_caption') or ('رسم توضيحي للسؤال' if q.get('image') else ''))
        ex = q.get('explanation') if isinstance(q.get('explanation'), dict) else {}
        ex.setdefault('summary', q.get('explain', ''))
        ex.setdefault('steps', [])
        ex.setdefault('similar_choices', [])
        q['explanation'] = ex
        q['explanation_mode'] = q.get('explanation_mode') or difficulty_mode(
            q.get('difficulty', 'متوسط'), image=q.get('image', ''), close_notes=None,
        )
        key = norm_text(q.get('question', '')) + (f"|{q.get('image')}" if q.get('image') else '')
        if key and key not in self.seen:
            self.seen.add(key)
            self.questions.append(q)
            self.id_counts[q.get('exam', '')] += 1

    def count(self, exam: str) -> int:
        return int(self.id_counts.get(exam, 0))

    def add(
        self, *, exam: str, category: str, skill: str, question: str,
        correct: str, distractors: list[str], explanation: str,
        steps: list[str] | None = None, difficulty: str = 'متوسط',
        keywords: list[str] | None = None, concept_id: str = '',
        misconception_id: str = '', passage: str = '', image: str = '',
        image_alt: str = '', hint: str = '', trap: str = '',
        close_notes: dict[str, str] | None = None, explanation_mode: str = '',
        source_pattern: str = '', time_sec: int = 60,
    ) -> bool:
        if self.count(exam) >= (TARGET_QUANT if exam == 'قدرات كمي' else TARGET_VERBAL):
            return False
        question = re.sub(r'\s+', ' ', question.strip())
        key = norm_text(question) + (f"|{image}" if image else '')
        if not key or key in self.seen:
            return False
        self.seen.add(key)
        correct = str(correct)
        distractors = normalize_units(correct, unique_choices(correct, distractors))
        correct_index = len(self.questions) % 4
        choices = distractors[:]
        choices.insert(correct_index, correct)
        notes = []
        for choice_text, note in (close_notes or {}).items():
            if choice_text in choices:
                notes.append({'choice_index': choices.index(choice_text), 'choice': choice_text, 'note': note})
        prefix = 'QDR-Q' if exam == 'قدرات كمي' else 'QDR-V'
        local_no = self.count(exam) + 1
        q = {
            'id': f'{prefix}-{local_no:04d}',
            'exam': exam,
            'eligible_tracks': ['علمي', 'أدبي'],
            'category': category,
            'skill': skill,
            'subject': 'قدرات',
            'unit': skill,
            'question': question,
            'choices': choices,
            'correct': correct_index,
            'answer': correct,
            'explain': explanation.strip(),
            'difficulty': difficulty,
            'time_per_question_sec': time_sec,
            'diagnostic': False,
            'keywords': keywords or [skill],
            'concept_id': concept_id or f"qudrat.{('quant' if exam == 'قدرات كمي' else 'verbal')}.{re.sub(r'\s+', '_', skill)}",
            'summary_block_id': '',
            'misconception_id': misconception_id,
            'display_variant': 'diagram' if image else ('passage' if passage else 'standard'),
            'source_status': 'original_generated_from_skill_map',
            'source_documents': SOURCE_DOCS,
            'source_pattern': source_pattern or skill,
            'copyright_method': 'original_question_new_values_new_wording',
            'editorial_status': 'qa_passed_internal',
            'release_eligible': True,
            'rights_status': 'original',
            'bank': 'قدرات موحد',
            'explanation_mode': difficulty_mode(difficulty, image=image, close_notes=close_notes, force=explanation_mode),
            'explanation': {
                'summary': explanation.strip(),
                'steps': steps or [],
                'similar_choices': notes,
            },
        }
        if trap:
            q['explanation']['trap'] = trap
        if hint:
            q['hint'] = hint
        if passage:
            q['passage'] = passage.strip()
        if image:
            q['image'] = image
            q['image_alt'] = image_alt or 'رسم توضيحي للسؤال'
            q['image_caption'] = ''
        self.questions.append(q)
        self.id_counts[exam] += 1
        return True


# ---------- SVG helpers (transparent backgrounds only) ----------

def write_svg(name: str, body: str, width: int = 640, height: int = 360) -> str:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / name
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
text{{font-family:"DejaVu Sans",Arial,sans-serif;fill:#17324d;font-weight:700}}
.shape{{stroke:#168bb7;stroke-width:6;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.soft{{stroke:#52bea1;stroke-width:5;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.guide{{stroke:#9bb0c0;stroke-width:3;fill:none;stroke-dasharray:8 8}}
.fill{{fill:#dff5ee;stroke:#52bea1;stroke-width:4}} .bar{{fill:#65b9da}} .label{{font-size:24px}} .small{{font-size:19px}}
</style>{body}</svg>'''
    path.write_text(svg, encoding='utf-8')
    ET.parse(path)
    return path.relative_to(ROOT).as_posix()


# ---------- Quantitative generators ----------

def add_percentage_questions(bank: Bank, n: int = 150):
    i = 0
    attempts = 0
    while i < n and bank.count('قدرات كمي') < TARGET_QUANT and attempts < n * 30:
        attempts += 1
        kind = i % 5
        if kind == 0:
            pct = RNG.choice([5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45])
            base = RNG.choice([80, 120, 150, 160, 180, 200, 240, 250, 300, 320, 400, 450, 500, 600])
            ans = Fraction(pct * base, 100)
            if ans.denominator != 1:
                continue
            c = fmt_num(ans)
            q = f'كم يساوي {pct}% من {base}؟'
            exp = f'نحوّل {pct}% إلى {pct}/100 ثم نضرب في {base}، فيكون الناتج {c}.'
            close = {fmt_num(base - ans): 'هذا يمثل الجزء المتبقي من العدد، لا قيمة النسبة المطلوبة.'}
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q,
                correct=c, distractors=[fmt_num(ans+5), fmt_num(base-ans), fmt_num(ans-5)], explanation=exp,
                difficulty='سهل', keywords=['نسبة مئوية','جزء من كل'], misconception_id='percent_of_number',
                close_notes=close if i % 4 == 0 else None)
        elif kind == 1:
            pct = RNG.choice([10, 15, 20, 25, 30, 40, 50])
            whole = RNG.choice([120, 160, 200, 240, 300, 360, 400, 480, 600])
            part = whole * pct // 100
            q = f'يمثل {part} نسبة {pct}% من عدد، فما ذلك العدد؟'
            exp = f'العدد الكامل = {part} ÷ ({pct}/100) = {whole}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q,
                correct=str(whole), distractors=[str(part+pct), str(whole-part), str(whole+pct)], explanation=exp,
                steps=[f'حوّل {pct}% إلى كسر عشري.', f'اقسم الجزء {part} على النسبة.'], difficulty='متوسط',
                keywords=['النسبة العكسية','إيجاد الكل'], misconception_id='reverse_percent')
        elif kind == 2:
            original = RNG.choice([120, 160, 200, 240, 300, 400, 500, 800])
            pct = RNG.choice([10, 15, 20, 25, 30])
            final = original * (100 - pct) // 100
            q = f'أصبح سعر سلعة بعد خصم {pct}% يساوي {final} ريالًا. كم كان سعرها قبل الخصم؟'
            exp = f'بعد الخصم بقي {100-pct}% من السعر، لذلك السعر الأصلي = {final} ÷ {(100-pct)/100:g} = {original} ريالًا.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q,
                correct=f'{original} ريال', distractors=[f'{final+pct} ريال', f'{original-pct} ريال', f'{final*100//pct} ريال'],
                explanation=exp, difficulty='متوسط', keywords=['خصم','سعر أصلي'], trap='لا تطرح نسبة الخصم من السعر النهائي؛ السعر النهائي هو الجزء المتبقي من الأصل.')
        elif kind == 3:
            start = RNG.choice([100, 120, 150, 200, 240, 250, 300, 400])
            pct = RNG.choice([10, 20, 25, 30, 40])
            end = start * (100 + pct) // 100
            q = f'زاد عدد من {start} إلى {end}. ما نسبة الزيادة؟'
            exp = f'مقدار الزيادة {end-start}، ونسبتها إلى العدد الأصلي = ({end-start} ÷ {start}) × 100 = {pct}%.'
            close = {f'{end-start}%': 'هذا يساوي مقدار الزيادة كعدد، وليس نسبتها إلى القيمة الأصلية.'}
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q,
                correct=f'{pct}%', distractors=[f'{end-start}%', f'{pct+5}%', f'{pct-5}%'], explanation=exp,
                difficulty='متوسط', keywords=['نسبة زيادة'], close_notes=close)
        else:
            bill = RNG.choice([200, 240, 300, 360, 400, 460, 500, 600, 800])
            pct = RNG.choice([5, 10, 15])
            tax = bill * pct // 100
            total = bill + tax
            q = f'فاتورة قيمتها {bill} ريالًا، أضيفت إليها رسوم بنسبة {pct}%. ما المبلغ النهائي؟'
            exp = f'قيمة الرسوم = {bill} × {pct}/100 = {tax}، ثم المبلغ النهائي = {bill} + {tax} = {total} ريالًا.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q,
                correct=f'{total} ريال', distractors=[f'{bill+pct} ريال', f'{bill-tax} ريال', f'{tax} ريال'], explanation=exp,
                difficulty='سهل', keywords=['ضريبة','زيادة نسبية'])
        i += int(ok)


def add_fraction_questions(bank: Bank, n: int = 120):
    ops = ['+','-','×','÷']
    i = 0
    attempts = 0
    while i < n and bank.count('قدرات كمي') < TARGET_QUANT and attempts < n * 30:
        attempts += 1
        kind = i % 5
        if kind == 0:
            a = Fraction(RNG.randint(1,9), RNG.choice([4,5,6,8,10,12]))
            b = Fraction(RNG.randint(1,9), RNG.choice([4,5,6,8,10,12]))
            op = RNG.choice(ops)
            if op == '-' and a <= b:
                a, b = b, a
            ans = {'+': a+b, '-': a-b, '×': a*b, '÷': a/b}[op]
            c = fmt_num(ans)
            q = f'ما ناتج {fmt_num(a)} {op} {fmt_num(b)} في أبسط صورة؟'
            exp = f'ننّفذ العملية على الكسور ثم نختصر الناتج، فنحصل على {c}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الكسور الاعتيادية', question=q,
                correct=c, distractors=[fmt_num(a+b), fmt_num(abs(a-b)), fmt_num(a*b)], explanation=exp,
                difficulty='متوسط', keywords=['كسور','تبسيط'], misconception_id='fraction_operation')
        elif kind == 1:
            den = RNG.choice([3,4,5,6,8,10,12])
            num = RNG.randint(1,den-1)
            whole = den * RNG.randint(6,20)
            ans = whole*num//den
            q = f'ما قيمة {num}/{den} من العدد {whole}؟'
            exp = f'نضرب {whole} في {num}/{den}؛ بعد الاختصار يكون الناتج {ans}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الكسور الاعتيادية', question=q,
                correct=str(ans), distractors=[str(whole//den), str(whole-num), str(ans+den)], explanation=exp,
                difficulty='سهل', keywords=['كسر من كمية'])
        elif kind == 2:
            den = RNG.choice([3,4,5,6,8,10,12])
            num = RNG.randint(1,den-1)
            whole = den * RNG.randint(6,20)
            part = whole*num//den
            q = f'إذا كان {num}/{den} من عدد يساوي {part}، فما العدد؟'
            exp = f'العدد = {part} × {den}/{num} = {whole}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الكسور الاعتيادية', question=q,
                correct=str(whole), distractors=[str(part+den), str(part*den), str(whole-num)], explanation=exp,
                difficulty='متوسط', keywords=['إيجاد الكل من كسر'])
        elif kind == 3:
            vals = [Fraction(RNG.randint(1,9), RNG.choice([5,6,7,8,9,10,11,12])) for _ in range(4)]
            vals = list(dict.fromkeys(vals))
            if len(vals) < 4:
                continue
            biggest = max(vals)
            q = 'أي الكسور الآتية أكبر؟'
            choices = [fmt_num(x) for x in vals]
            c = fmt_num(biggest)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الكسور الاعتيادية', question=q + ' ' + '، '.join(choices),
                correct=c, distractors=[x for x in choices if x != c], explanation=f'بمقارنة الكسور بعد توحيد المقامات أو تحويلها إلى أعداد عشرية نجد أن {c} هو الأكبر.',
                difficulty='متوسط', keywords=['مقارنة الكسور'])
        else:
            a_den = RNG.choice([3,4,5,6,8])
            a_num = RNG.randint(1,a_den-1)
            b_den = RNG.choice([4,5,6,8,10])
            b_num = RNG.randint(1,b_den-1)
            total = Fraction(a_num,a_den)+Fraction(b_num,b_den)
            if total >= 1:
                continue
            q = f'خزان ممتلئ بمقدار {a_num}/{a_den} من سعته، ثم أضيف إليه {b_num}/{b_den} من سعته. كم أصبح الجزء الممتلئ؟'
            c = fmt_num(total)
            exp = f'نجمع الكسرين بعد توحيد المقامات: {a_num}/{a_den} + {b_num}/{b_den} = {c}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الكسور الاعتيادية', question=q,
                correct=c, distractors=[fmt_num(Fraction(a_num+b_num,a_den+b_den)), fmt_num(abs(Fraction(a_num,a_den)-Fraction(b_num,b_den))), '1'], explanation=exp,
                difficulty='متوسط', keywords=['جمع الكسور','سعة'])
        i += int(ok)


def add_decimal_questions(bank: Bank, n: int = 90):
    i = 0
    attempts = 0
    while i < n and bank.count('قدرات كمي') < TARGET_QUANT and attempts < n * 30:
        attempts += 1
        kind = i % 5
        if kind == 0:
            a = RNG.randint(100,999)/100
            b = RNG.randint(10,999)/1000
            ans = a+b
            q = f'ما ناتج {fmt_num(a)} + {fmt_num(b)}؟'
            c = fmt_num(ans)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الأعداد العشرية', question=q,
                correct=c, distractors=[fmt_num(ans+0.1), fmt_num(abs(a-b)), fmt_num(ans*10)], explanation=f'نرتب الفواصل العشرية ثم نجمع، فنحصل على {c}.', difficulty='سهل')
        elif kind == 1:
            a = RNG.randint(500,2000)/100
            b = RNG.randint(100,499)/100
            ans = a-b
            q = f'ما ناتج {fmt_num(a)} - {fmt_num(b)}؟'
            c = fmt_num(ans)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الأعداد العشرية', question=q,
                correct=c, distractors=[fmt_num(ans+1), fmt_num(a+b), fmt_num(ans/10)], explanation=f'نضع الفاصلتين تحت بعضهما ثم نطرح، فيكون الناتج {c}.', difficulty='سهل')
        elif kind == 2:
            x = RNG.choice([0.0042,0.036,0.075,0.125,0.48,1.25,2.4])
            power = RNG.choice([10,100,1000])
            ans = x*power
            q = f'ما قيمة {fmt_num(x)} × {power}؟'
            c = fmt_num(ans)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الأعداد العشرية', question=q,
                correct=c, distractors=[fmt_num(x/power), fmt_num(ans*10), fmt_num(ans/10)], explanation=f'نحرك الفاصلة إلى اليمين بعدد أصفار {power}، فيكون الناتج {c}.', difficulty='سهل')
        elif kind == 3:
            x = RNG.randint(1000,9999)/100
            power = RNG.choice([10,100,1000])
            ans = x/power
            q = f'ما قيمة {fmt_num(x)} ÷ {power}؟'
            c = fmt_num(ans)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الأعداد العشرية', question=q,
                correct=c, distractors=[fmt_num(x*power), fmt_num(ans*10), fmt_num(ans/10)], explanation=f'نحرك الفاصلة إلى اليسار بعدد أصفار {power}، فنحصل على {c}.', difficulty='سهل')
        else:
            x = RNG.randint(10000,99999)/1000
            places = RNG.choice([1,2])
            ans = round(x, places)
            label = 'جزء من عشرة' if places == 1 else 'جزء من مئة'
            q = f'قرّب العدد {fmt_num(x)} إلى أقرب {label}.'
            c = fmt_num(ans)
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='الأعداد العشرية', question=q,
                correct=c, distractors=[fmt_num(math.floor(x*10**places)/10**places), fmt_num(math.ceil(x*10**places)/10**places), fmt_num(round(x))], explanation=f'ننظر إلى الخانة التالية لخانة التقريب؛ الناتج هو {c}.', difficulty='سهل')
        i += int(ok)


def add_ratio_questions(bank: Bank, n: int = 120):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%4
        a,b=RNG.randint(1,6),RNG.randint(2,8)
        if a==b: continue
        k=RNG.randint(4,15)
        if kind==0:
            total=(a+b)*k
            q=f'نسبة الأقلام الزرقاء إلى السوداء {a} : {b}، وكان مجموعها {total}. كم قلمًا أسود؟'
            ans=b*k
            exp=f'مجموع أجزاء النسبة {a+b}، وقيمة الجزء {total} ÷ {a+b} = {k}، إذن الأسود {b} × {k} = {ans}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='النسبة والتناسب',question=q,correct=str(ans),distractors=[str(a*k),str(total//2),str(ans+k)],explanation=exp,difficulty='متوسط')
        elif kind==1:
            count=RNG.randint(4,12); unit=RNG.randint(3,15); wanted=RNG.randint(13,24)
            cost=count*unit; ans=wanted*unit
            q=f'إذا كان ثمن {count} دفاتر {cost} ريالًا، فكم ثمن {wanted} دفترًا بالسعر نفسه؟'
            exp=f'سعر الدفتر = {cost} ÷ {count} = {unit} ريالات، ثم {wanted} × {unit} = {ans} ريالًا.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='النسبة والتناسب',question=q,correct=f'{ans} ريال',distractors=[f'{cost+wanted} ريال',f'{wanted+unit} ريال',f'{ans-unit} ريال'],explanation=exp,difficulty='سهل')
        elif kind==2:
            workers=RNG.choice([4,5,6,8,10,12]); days=RNG.choice([12,15,18,20,24,30]); new=RNG.choice([workers+2,workers+4,workers*2])
            if workers*days%new: continue
            ans=workers*days//new
            q=f'ينجز {workers} عمال عملاً في {days} يومًا بالمعدل نفسه. كم يومًا يحتاج {new} عمال؟'
            exp=f'العمل ثابت، لذلك {workers} × {days} = {new} × الزمن، ومنه الزمن = {ans} يومًا.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='النسبة والتناسب',question=q,correct=f'{ans} يوم',distractors=[f'{days} يوم',f'{days+ans} يوم',f'{max(1,days-ans)} يوم'],explanation=exp,difficulty='متوسط',trap='العلاقة عكسية: زيادة العمال تقلل الزمن.')
        else:
            scale=RNG.choice([100000,200000,250000,500000]); cm=RNG.choice([2,3,4,5,6,8]); km=cm*scale/100000
            q=f'مقياس رسم خريطة 1 : {scale}، وكانت المسافة عليها {cm} سم. ما المسافة الحقيقية بالكيلومترات؟'
            c=fmt_num(km)
            exp=f'المسافة الحقيقية = {cm} × {scale} سم، ثم نقسم على 100000 للتحويل إلى كيلومترات، فنحصل على {c} كم.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='النسبة والتناسب',question=q,correct=f'{c} كم',distractors=[f'{cm} كم',f'{fmt_num(km*10)} كم',f'{fmt_num(km/10)} كم'],explanation=exp,difficulty='متوسط')
        i+=int(ok)


def add_divisibility_questions(bank: Bank,n:int=90):
    i=0
    attempts=0
    rules={2:'رقم الآحاد زوجي',3:'مجموع الأرقام يقبل القسمة على 3',4:'الرقمان الأخيران يقبلان القسمة على 4',5:'رقم الآحاد 0 أو 5',6:'العدد يقبل القسمة على 2 و3 معًا',9:'مجموع الأرقام يقبل القسمة على 9',10:'رقم الآحاد 0',11:'الفرق بين مجموع الخانات المتبادلة يقبل القسمة على 11'}
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%3
        if kind==0:
            d=RNG.choice(list(rules)); base=RNG.randint(20,900); num=base*d
            wrong=[num+1,num+2,num+d//2 if d>2 else num+3]
            q=f'من بين الأعداد {num}، {wrong[0]}، {wrong[1]}، {wrong[2]}: أيها يقبل القسمة على {d} دون باق؟'
            exp=f'{num} يقبل القسمة على {d}. قاعدة التحقق: {rules[d]}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='قابلية القسمة والأعداد الأولية',question=q,correct=str(num),distractors=[str(x) for x in wrong],explanation=exp,difficulty='سهل',keywords=['قابلية القسمة',str(d)])
        elif kind==1:
            primes=[11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
            p=RNG.choice(primes); comps=[p+1,p+2 if (p+2)%2==0 else p+3,p*2]
            q=f'من بين الأعداد {p}، {comps[0]}، {comps[1]}، {comps[2]}: أيها عدد أولي؟'
            exp=f'{p} لا يقبل القسمة إلا على 1 وعلى نفسه، بينما بقية الخيارات أعداد مركبة.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='قابلية القسمة والأعداد الأولية',question=q,correct=str(p),distractors=[str(x) for x in comps],explanation=exp,difficulty='متوسط',keywords=['عدد أولي'])
        else:
            d=RNG.choice([3,4,5,6,8,9,11]); num=RNG.randint(100,999); rem=num%d
            q=f'ما باقي قسمة {num} على {d}؟'
            exp=f'نكتب {num} = {num//d} × {d} + {rem}، إذن الباقي {rem}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل حسابية',skill='قابلية القسمة والأعداد الأولية',question=q,correct=str(rem),distractors=[str((rem+1)%d),str(d),str(num//d)],explanation=exp,difficulty='سهل')
        i+=int(ok)


def add_roots_questions(bank: Bank,n:int=90):
    i=0
    attempts=0
    squares=[4,9,16,25,36,49,64,81,100,121,144,169,196,225]
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%4
        if kind==0:
            s=RNG.choice(squares); m=RNG.choice([2,3,5,6,7,10]); val=s*m; root=int(math.isqrt(s)); c=f'{root}√{m}'
            q=f'بسّط √{val}.'
            exp=f'نكتب {val} = {s} × {m}، لذلك √{val} = √{s} × √{m} = {c}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='الجذور والأسس',question=q,correct=c,distractors=[f'{root+1}√{m}',f'√{m}',str(root*m)],explanation=exp,difficulty='متوسط')
        elif kind==1:
            a=RNG.randint(2,8); b=RNG.randint(2,5); cval=a**b
            q=f'ما قيمة {a}^{b}؟'
            exp=f'{a}^{b} يعني ضرب {a} في نفسه {b} مرات، والناتج {cval}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='الجذور والأسس',question=q,correct=str(cval),distractors=[str(a*b),str(a**(b-1)),str(cval+a)],explanation=exp,difficulty='سهل')
        elif kind==2:
            a=RNG.randint(2,6); m=RNG.randint(2,5); n=RNG.randint(1,4); ans=a**(m+n)
            q=f'ما قيمة {a}^{m} × {a}^{n}؟'
            exp=f'عند ضرب قوتين لهما الأساس نفسه نجمع الأسس: {a}^{m+n} = {ans}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='الجذور والأسس',question=q,correct=str(ans),distractors=[str(a**(m*n)),str(a**abs(m-n)),str(a**m+a**n)],explanation=exp,difficulty='متوسط',trap='لا نضرب الأسس عند ضرب قوتين لهما الأساس نفسه؛ بل نجمعها.')
        else:
            a=RNG.randint(2,9); b=RNG.randint(2,9); ans=math.sqrt(a*a*b*b)
            q=f'ما قيمة √({a*a} × {b*b})؟'
            c=str(int(ans))
            exp=f'√({a*a} × {b*b}) = {a} × {b} = {c}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='الجذور والأسس',question=q,correct=c,distractors=[str(a+b),str(a*b*2),str(abs(a-b))],explanation=exp,difficulty='سهل')
        i+=int(ok)


def add_average_questions(bank: Bank,n:int=90):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%4
        if kind==0:
            vals=[RNG.randint(10,90) for _ in range(RNG.choice([4,5,6]))]
            s=sum(vals); k=len(vals)
            if s%k: continue
            avg=s//k
            q=f'ما المتوسط الحسابي للأعداد: {"، ".join(map(str,vals))}؟'
            exp=f'نجمع القيم فنحصل على {s}، ثم نقسم على عددها {k}، فيكون المتوسط {avg}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='المتوسط الحسابي',question=q,correct=str(avg),distractors=[str(max(vals)),str(min(vals)),str(s)],explanation=exp,difficulty='سهل')
        elif kind==1:
            avg=RNG.randint(20,80); k=RNG.choice([4,5,6]); missing=RNG.randint(10,90); known_sum=avg*k-missing
            if known_sum<=0: continue
            parts=[known_sum//(k-1)]*(k-2); parts.append(known_sum-sum(parts))
            q=f'متوسط {k} أعداد هو {avg}. إذا كان مجموع {k-1} منها {known_sum}، فما العدد المتبقي؟'
            exp=f'مجموع الأعداد كلها = {avg} × {k} = {avg*k}، والمتبقي = {avg*k} - {known_sum} = {missing}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='المتوسط الحسابي',question=q,correct=str(missing),distractors=[str(avg),str(known_sum//(k-1)),str(missing+k)],explanation=exp,difficulty='متوسط')
        elif kind==2:
            vals=sorted([RNG.randint(5,90) for _ in range(7)])
            med=vals[3]
            q=f'ما الوسيط للقيم: {"، ".join(map(str,vals))}؟'
            exp=f'بعد ترتيب 7 قيم تكون القيمة الرابعة هي الوسيط، وهي {med}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='الإحصاء الوصفي',question=q,correct=str(med),distractors=[str(vals[2]),str(vals[4]),str(round(sum(vals)/7))],explanation=exp,difficulty='سهل')
        else:
            mode=RNG.randint(5,20); vals=[mode,mode,mode,RNG.randint(1,30),RNG.randint(1,30),RNG.randint(1,30)]
            RNG.shuffle(vals)
            q=f'ما المنوال للقيم: {"، ".join(map(str,vals))}؟'
            exp=f'المنوال هو القيمة الأكثر تكرارًا، وهي {mode}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='الإحصاء الوصفي',question=q,correct=str(mode),distractors=[str(min(vals)),str(max(vals)),str(round(sum(vals)/len(vals)))],explanation=exp,difficulty='سهل')
        i+=int(ok)


def add_speed_questions(bank: Bank,n:int=110):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%5
        if kind==0:
            speed=RNG.choice([40,50,60,70,80,90,100,120]); time=RNG.choice([2,3,4,5]); dist=speed*time
            q=f'تسير سيارة بسرعة {speed} كم/س مدة {time} ساعات. ما المسافة التي تقطعها؟'
            exp=f'المسافة = السرعة × الزمن = {speed} × {time} = {dist} كم.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='السرعة والمسافة والزمن',question=q,correct=f'{dist} كم',distractors=[f'{speed+time} كم',f'{dist-speed} كم',f'{dist+speed} كم'],explanation=exp,difficulty='سهل')
        elif kind==1:
            time=RNG.choice([2,3,4,5]); speed=RNG.choice([40,50,60,70,80,90]); dist=time*speed
            q=f'قطع قطار مسافة {dist} كم في {time} ساعات. ما سرعته المتوسطة؟'
            exp=f'السرعة = المسافة ÷ الزمن = {dist} ÷ {time} = {speed} كم/س.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='السرعة والمسافة والزمن',question=q,correct=f'{speed} كم/س',distractors=[f'{dist-time} كم/س',f'{speed+time} كم/س',f'{dist*time} كم/س'],explanation=exp,difficulty='سهل')
        elif kind==2:
            slower=RNG.choice([40,50,60,70]); faster=slower+RNG.choice([20,30,40]); gap=RNG.choice([60,80,90,120,150,180])
            if gap%(faster-slower): continue
            t=gap//(faster-slower)
            q=f'تتحرك سيارة بسرعة {slower} كم/س، وتتبعها سيارة أسرع بسرعة {faster} كم/س وبينهما {gap} كم. بعد كم ساعة تلحق بها؟'
            exp=f'سرعة الاقتراب = {faster} - {slower} = {faster-slower} كم/س، والزمن = {gap} ÷ {faster-slower} = {t} ساعات.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='السرعة والمسافة والزمن',question=q,correct=f'{t} ساعة',distractors=[f'{gap//faster} ساعة',f'{gap//slower} ساعة',f'{t+1} ساعة'],explanation=exp,difficulty='متوسط',trap='في مسائل اللحاق نستخدم فرق السرعتين، لا مجموعهما.')
        elif kind==3:
            s1=RNG.choice([40,50,60,70]); s2=RNG.choice([60,70,80,90]); t=RNG.choice([2,3,4]); dist=(s1+s2)*t
            q=f'انطلقت مركبتان في اتجاهين متعاكسين بسرعتي {s1} و{s2} كم/س. كم تصبح المسافة بينهما بعد {t} ساعات؟'
            exp=f'لأن الاتجاهين متعاكسان نجمع السرعتين: ({s1}+{s2}) × {t} = {dist} كم.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='السرعة والمسافة والزمن',question=q,correct=f'{dist} كم',distractors=[f'{abs(s2-s1)*t} كم',f'{(s1+s2)} كم',f'{s1*s2} كم'],explanation=exp,difficulty='متوسط')
        else:
            kmh=RNG.choice([36,54,72,90,108]); ms=kmh*5//18
            q=f'حوّل السرعة {kmh} كم/س إلى متر/ثانية.'
            exp=f'للتحويل من كم/س إلى م/ث نضرب في 5/18: {kmh} × 5/18 = {ms} م/ث.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='السرعة والمسافة والزمن',question=q,correct=f'{ms} م/ث',distractors=[f'{kmh*18//5} م/ث',f'{ms+5} م/ث',f'{kmh//2} م/ث'],explanation=exp,difficulty='متوسط')
        i+=int(ok)


def add_word_problem_questions(bank: Bank,n:int=260):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%6
        if kind==0:  # ages
            age=RNG.randint(10,30); older=RNG.randint(3,12); years=RNG.randint(2,8)
            q=f'عمر سارة الآن {age} سنة، وأختها أكبر منها بـ {older} سنوات. كم يكون مجموع عمريهما بعد {years} سنوات؟'
            ans=age+(age+older)+2*years
            exp=f'عمر الأخت الآن {age+older}. بعد {years} سنوات يصبح المجموع ({age}+{years}) + ({age+older}+{years}) = {ans}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='مسائل الأعمار',question=q,correct=f'{ans} سنة',distractors=[f'{ans-years} سنة',f'{2*age+older} سنة',f'{ans+years} سنة'],explanation=exp,difficulty='سهل')
        elif kind==1:  # work
            a=RNG.choice([4,5,6,8,10,12]); days=RNG.choice([12,15,18,20,24,30]); b=RNG.choice([a+2,a+4,a*2])
            if a*days%b: continue
            ans=a*days//b
            q=f'يستطيع {a} عمال إنجاز مشروع في {days} يومًا. كم يومًا يحتاج {b} عمال بالمعدل نفسه؟'
            exp=f'عدد أيام العمل الكلية ثابت: {a} × {days} = {a*days} يوم-عامل، لذلك الزمن = {a*days} ÷ {b} = {ans} يومًا.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='العمل والإنجاز',question=q,correct=f'{ans} يوم',distractors=[f'{days} يوم',f'{ans+a} يوم',f'{days-ans} يوم'],explanation=exp,difficulty='متوسط')
        elif kind==2:  # profit
            cost=RNG.choice([80,100,120,150,200,240,300,400]); pct=RNG.choice([10,15,20,25,30]); sell=cost*(100+pct)//100
            q=f'اشترى تاجر سلعة بـ {cost} ريالًا وباعها بـ {sell} ريالًا. ما نسبة الربح؟'
            exp=f'الربح = {sell-cost} ريالًا، ونسبته إلى سعر الشراء = ({sell-cost} ÷ {cost}) × 100 = {pct}%.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='الربح والخسارة',question=q,correct=f'{pct}%',distractors=[f'{sell-cost}%',f'{pct+5}%',f'{pct-5}%'],explanation=exp,difficulty='متوسط',close_notes={f'{sell-cost}%':'هذا مقدار الربح كعدد، وليس نسبته المئوية.'})
        elif kind==3:  # mixture
            total=RNG.choice([20,25,30,40,50,60]); ratio=RNG.choice([(1,4),(2,3),(3,5),(1,5)]); a,b=ratio
            if total%(a+b): continue
            first=total*a//(a+b)
            q=f'خليط مكوّن من عصير وماء بنسبة {a} : {b}، وحجمه {total} لترًا. كم لترًا من العصير؟'
            exp=f'مجموع الأجزاء {a+b}، وقيمة الجزء {total} ÷ {a+b} = {total//(a+b)}، والعصير {a} أجزاء = {first} لترات.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='الخلط والتركيز',question=q,correct=f'{first} لتر',distractors=[f'{total-first} لتر',f'{a+b} لتر',f'{first+a} لتر'],explanation=exp,difficulty='متوسط')
        elif kind==4:  # counting
            shirts=RNG.randint(3,7); pants=RNG.randint(2,6); shoes=RNG.randint(2,4); ans=shirts*pants*shoes
            q=f'لدى شخص {shirts} قمصان و{pants} سراويل و{shoes} أحذية. كم مظهرًا مختلفًا يمكن تكوينه باختيار واحد من كل نوع؟'
            exp=f'نستخدم مبدأ العد: {shirts} × {pants} × {shoes} = {ans} مظهرًا.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='مبدأ العد',question=q,correct=str(ans),distractors=[str(shirts+pants+shoes),str(shirts*pants),str(ans-shoes)],explanation=exp,difficulty='سهل')
        else:  # inclusion exclusion
            total=RNG.choice([40,50,60,80,100]); a=RNG.randint(total//3,total//2); b=RNG.randint(total//3,total//2); both=RNG.randint(5,min(a,b)//2); union=a+b-both
            if union>total: continue
            neither=total-union
            q=f'في مجموعة من {total} طالبًا، يفضّل {a} منهم القراءة و{b} الرياضة، و{both} يفضّلون النشاطين. كم طالبًا لا يفضّل أيًا منهما؟'
            exp=f'عدد من يفضّلون نشاطًا واحدًا على الأقل = {a}+{b}-{both} = {union}، إذن من لا يفضّل أيًا منهما = {total}-{union} = {neither}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='مبدأ الشمول والاستبعاد',question=q,correct=str(neither),distractors=[str(union),str(total-a-b),str(a+b)],explanation=exp,difficulty='صعب')
        i+=int(ok)


def add_algebra_questions(bank: Bank,n:int=330):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%5
        if kind==0:
            x=RNG.randint(-12,30); a=RNG.randint(2,9); b=RNG.randint(-20,20); c=a*x+b
            sign='+' if b>=0 else '-'; q=f'إذا كان {a}س {sign} {abs(b)} = {c}، فما قيمة س؟'
            exp=f'ننقل {b} إلى الطرف الآخر ثم نقسم على {a}: س = ({c} - ({b})) ÷ {a} = {x}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='المعادلات الخطية',question=q,correct=str(x),distractors=[str(x+1),str(x-1),str(c//a)],explanation=exp,difficulty='متوسط')
        elif kind==1:
            x=RNG.randint(2,15); a=RNG.randint(2,6); b=RNG.randint(1,12); val=a*x+b
            q=f'إذا كانت س = {x}، فما قيمة {a}س + {b}؟'
            exp=f'بالتعويض عن س بـ {x}: {a} × {x} + {b} = {val}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='التعويض والعلاقات الجبرية',question=q,correct=str(val),distractors=[str(a+b+x),str(val-b),str(val+a)],explanation=exp,difficulty='سهل')
        elif kind==2:
            x=RNG.randint(2,12); m=RNG.randint(2,8); b=RNG.randint(-10,10); y=m*x+b
            sign='+' if b>=0 else '-'; q=f'إذا كانت الدالة د(س) = {m}س {sign} {abs(b)}، فما قيمة د({x})؟'
            exp=f'نعوّض س = {x}: د({x}) = {m} × {x} + ({b}) = {y}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='الدوال والتناسب',question=q,correct=str(y),distractors=[str(m+x+b),str(y+m),str(y-b)],explanation=exp,difficulty='سهل')
        elif kind==3:
            a=RNG.randint(2,9); bound=RNG.randint(10,60); x=bound//a
            q=f'أي القيم الآتية تحقق المتباينة {a}س < {bound}؟'
            correct=x-1
            exp=f'بقسمة الطرفين على {a} نحصل على س < {bound/a:g}، لذا القيمة {correct} تحقق المتباينة.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='المتباينات والقيمة المطلقة',question=q,correct=str(correct),distractors=[str(math.ceil(bound/a)),str(math.ceil(bound/a)+1),str(bound)],explanation=exp,difficulty='متوسط')
        else:
            start=RNG.randint(1,20); diff=RNG.randint(2,8); length=RNG.choice([5,6,7]); seq=[start+diff*k for k in range(length)]; nxt=seq[-1]+diff
            q=f'أكمل النمط: {"، ".join(map(str,seq))}، ...'
            exp=f'الفرق ثابت ويساوي {diff}، لذلك الحد التالي = {seq[-1]} + {diff} = {nxt}.'
            ok=bank.add(exam='قدرات كمي',category='الجبر',skill='المتتابعات والأنماط',question=q,correct=str(nxt),distractors=[str(nxt+diff),str(nxt-1),str(seq[-1]*2)],explanation=exp,difficulty='سهل')
        i+=int(ok)


def add_probability_questions(bank: Bank,n:int=90):
    i=0
    attempts=0
    while i<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=i%3
        if kind==0:
            red=RNG.randint(2,8); blue=RNG.randint(2,8); green=RNG.randint(1,6); total=red+blue+green
            color, count=RNG.choice([('حمراء',red),('زرقاء',blue),('خضراء',green)])
            frac=Fraction(count,total); c=fmt_num(frac)
            q=f'صندوق فيه {red} كرات حمراء و{blue} زرقاء و{green} خضراء. ما احتمال سحب كرة {color}؟'
            exp=f'عدد النتائج المناسبة {count} من أصل {total}، لذا الاحتمال = {count}/{total} = {c}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='الاحتمالات',question=q,correct=c,distractors=[fmt_num(Fraction(total-count,total)),fmt_num(Fraction(1,total)),str(count)],explanation=exp,difficulty='متوسط')
        elif kind==1:
            sides=RNG.choice([6,8,10,12]); target=RNG.randint(1,sides)
            q=f'عند رمي نرد منتظم له {sides} أوجه مرقمة من 1 إلى {sides}، ما احتمال ظهور العدد {target}؟'
            c=f'1/{sides}'; exp=f'هناك نتيجة واحدة مناسبة من أصل {sides} نتائج متساوية الاحتمال، إذن الاحتمال {c}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='الاحتمالات',question=q,correct=c,distractors=[f'{target}/{sides}',f'1/{sides-1}',str(target)],explanation=exp,difficulty='سهل')
        else:
            n=RNG.randint(5,12); total=n*(n-1)//2
            q=f'إذا صافح كل واحد من {n} أشخاص كل شخص آخر مرة واحدة، فكم مصافحة تحدث؟'
            exp=f'عدد الأزواج = {n} × {n-1} ÷ 2 = {total}.'
            ok=bank.add(exam='قدرات كمي',category='مسائل تطبيقية',skill='مبدأ العد',question=q,correct=str(total),distractors=[str(n*(n-1)),str(n+n-1),str(total-n)],explanation=exp,difficulty='متوسط')
        i+=int(ok)


def add_visual_questions(bank: Bank,n:int=120):
    created=0; idx=1
    attempts=0
    while created<n and bank.count('قدرات كمي')<TARGET_QUANT and attempts<n*30:
        attempts+=1
        kind=created%6
        if kind==0:  # rectangle
            w=RNG.randint(5,18); h=RNG.randint(3,12); ans=w*h
            body=f'<rect class="shape" x="120" y="85" width="400" height="210" rx="6"/><text class="label" x="310" y="325">{w} سم</text><text class="label" x="52" y="200">{h} سم</text>'
            image=write_svg(f'rectangle_{idx}.svg',body)
            q='ما مساحة المستطيل الموضح في الشكل؟'
            exp=f'مساحة المستطيل = الطول × العرض = {w} × {h} = {ans} سم².'
            ok=bank.add(exam='قدرات كمي',category='الهندسة',skill='المستطيلات والمربعات',question=q+f' (الأبعاد {w} سم و{h} سم)',correct=f'{ans} سم²',distractors=[f'{2*(w+h)} سم²',f'{w+h} سم²',f'{ans+h} سم²'],explanation=exp,difficulty='سهل',image=image,image_alt=f'مستطيل طوله {w} سم وعرضه {h} سم',explanation_mode='brief')
        elif kind==1:  # triangle
            base=RNG.choice([8,10,12,14,16,18,20]); height=RNG.choice([5,6,8,9,10,12]); ans=base*height//2
            body=f'<path class="shape" d="M100 285 L540 285 L320 70 Z"/><line class="guide" x1="320" y1="70" x2="320" y2="285"/><text class="label" x="285" y="330">{base} سم</text><text class="label" x="330" y="180">{height} سم</text><path class="soft" d="M320 265 h20 v20"/>'
            image=write_svg(f'triangle_{idx}.svg',body)
            exp=f'مساحة المثلث = 1/2 × القاعدة × الارتفاع = 1/2 × {base} × {height} = {ans} سم².'
            ok=bank.add(exam='قدرات كمي',category='الهندسة',skill='المثلثات',question='ما مساحة المثلث الموضح؟'+f' قاعدته {base} سم وارتفاعه {height} سم.',correct=f'{ans} سم²',distractors=[f'{base*height} سم²',f'{base+height} سم²',f'{ans+height} سم²'],explanation=exp,difficulty='سهل',image=image,image_alt=f'مثلث قاعدته {base} سم وارتفاعه العمودي {height} سم',close_notes={f'{base*height} سم²':'هذا ناتج القاعدة × الارتفاع، وهو مساحة مستطيل، أما المثلث فنأخذ نصفه.'})
        elif kind==2:  # circle
            r=RNG.choice([3,4,5,6,7,8,10]); ans=3.14*r*r
            c=fmt_num(ans)
            body=f'<circle class="shape" cx="320" cy="180" r="125"/><line class="soft" x1="320" y1="180" x2="445" y2="180"/><text class="label" x="350" y="165">{r} سم</text>'
            image=write_svg(f'circle_{idx}.svg',body)
            exp=f'مساحة الدائرة = ط × نق² = 3.14 × {r}² = {c} سم².'
            per=fmt_num(2*3.14*r)
            ok=bank.add(exam='قدرات كمي',category='الهندسة',skill='الدوائر',question='ما مساحة الدائرة الموضحة؟'+f' نصف قطرها {r} سم.',correct=f'{c} سم²',distractors=[f'{per} سم²',f'{fmt_num(3.14*r)} سم²',f'{fmt_num(ans*2)} سم²'],explanation=exp,difficulty='متوسط',image=image,image_alt=f'دائرة نصف قطرها {r} سم',close_notes={f'{per} سم²':'هذا يساوي محيط الدائرة 2ط نق، وليس مساحتها.'})
        elif kind==3:  # bar chart
            vals=[RNG.randint(4,18) for _ in range(4)]; labels=['الأحد','الاثنين','الثلاثاء','الأربعاء']; target=RNG.randrange(4); ans=vals[target]
            bars=[]
            for j,v in enumerate(vals):
                x=100+j*120; y=300-v*12; bars.append(f'<rect class="bar" x="{x}" y="{y}" width="55" height="{v*12}" rx="5"/><text class="small" x="{x-8}" y="330">{labels[j]}</text>')
            body='<line class="shape" x1="70" y1="300" x2="580" y2="300"/><line class="shape" x1="70" y1="60" x2="70" y2="300"/>'+''.join(bars)
            image=write_svg(f'bar_{idx}.svg',body)
            q=f'وفق الرسم البياني، ما قيمة يوم {labels[target]}؟'
            exp=f'نقرأ ارتفاع العمود الخاص بيوم {labels[target]} فنجد أنه يمثل القيمة {ans}.'
            ok=bank.add(exam='قدرات كمي',category='الإحصاء',skill='قراءة الجداول والرسوم',question=q,correct=str(ans),distractors=[str(vals[(target+1)%4]),str(max(vals)),str(sum(vals))],explanation=exp,difficulty='سهل',image=image,image_alt='رسم أعمدة لأربعة أيام',explanation_mode='none')
        elif kind==4:  # composite L
            W=RNG.randint(10,18); H=RNG.randint(7,13); cutw=RNG.randint(2,W-4); cuth=RNG.randint(2,H-3); ans=W*H-cutw*cuth
            sx,sy=20,18; # scale
            x0,y0=120,65
            p=f'M{x0} {y0} H{x0+W*sx} V{y0+H*sy} H{x0+(W-cutw)*sx} V{y0+(H-cuth)*sy} H{x0} Z'
            body=f'<path class="shape" d="{p}"/><text class="small" x="{x0+W*sx/2-20}" y="{y0-12}">{W} سم</text><text class="small" x="{x0-70}" y="{y0+H*sy/2}">{H} سم</text><text class="small" x="{x0+(W-cutw)*sx+10}" y="{y0+(H-cuth/2)*sy}">{cutw}×{cuth}</text>'
            image=write_svg(f'composite_{idx}.svg',body)
            exp=f'مساحة المستطيل الكبير {W}×{H}={W*H}، ومساحة الجزء المزال {cutw}×{cuth}={cutw*cuth}، فالمتبقي {ans} سم².'
            ok=bank.add(exam='قدرات كمي',category='الهندسة',skill='مساحات مركبة',question='ما مساحة الجزء المتبقي في الشكل المركب الموضح؟',correct=f'{ans} سم²',distractors=[f'{W*H} سم²',f'{cutw*cuth} سم²',f'{ans+cutw*cuth} سم²'],explanation=exp,difficulty='متوسط',image=image,image_alt='شكل على هيئة حرف لام بأبعاد موضحة')
        else:  # coordinate midpoint
            x1=RNG.randint(-8,2); y1=RNG.randint(-6,4); x2=x1+RNG.choice([4,6,8,10]); y2=y1+RNG.choice([4,6,8,10]); mx=(x1+x2)//2; my=(y1+y2)//2
            # simple coordinate drawing
            def mapx(x): return 320+x*20
            def mapy(y): return 180-y*20
            body='<line class="guide" x1="60" y1="180" x2="580" y2="180"/><line class="guide" x1="320" y1="40" x2="320" y2="330"/>'+\
                 f'<circle class="fill" cx="{mapx(x1)}" cy="{mapy(y1)}" r="9"/><circle class="fill" cx="{mapx(x2)}" cy="{mapy(y2)}" r="9"/><line class="soft" x1="{mapx(x1)}" y1="{mapy(y1)}" x2="{mapx(x2)}" y2="{mapy(y2)}"/><text class="small" x="{mapx(x1)-20}" y="{mapy(y1)-15}">أ</text><text class="small" x="{mapx(x2)+10}" y="{mapy(y2)-10}">ب</text>'
            image=write_svg(f'midpoint_{idx}.svg',body)
            c=f'({mx}، {my})'; q=f'إحداثيا النقطتين أ({x1}، {y1}) وب({x2}، {y2}). ما إحداثيا نقطة المنتصف؟'
            exp=f'نقطة المنتصف = (({x1}+{x2})/2، ({y1}+{y2})/2) = {c}.'
            ok=bank.add(exam='قدرات كمي',category='الهندسة',skill='الإحداثيات والأشكال المركبة',question=q,correct=c,distractors=[f'({x1+x2}، {y1+y2})',f'({mx+1}، {my})',f'({mx}، {my+1})'],explanation=exp,difficulty='متوسط',image=image,image_alt='مستوى إحداثي عليه نقطتان موصولتان')
        if ok:
            created+=1; idx+=1


# ---------- Verbal generators ----------
RELATIONS = {
    'أداة ووظيفتها': [
        ('قلم','كتابة'),('منشار','قطع'),('مفتاح','فتح'),('ميزان','وزن'),('بوصلة','تحديد الاتجاه'),('مطرقة','طرق'),('مجهر','تكبير'),('محراث','حرث'),('إبرة','خياطة'),('فرشاة','طلاء'),('مطفأة','إخماد'),('منبه','تنبيه'),('مصباح','إضاءة'),('مقياس','قياس'),('مكبح','إيقاف'),('مضخة','رفع الماء'),('غربال','تنقية'),('عدسة','تكبير'),('مروحة','تهوية'),('رادار','رصد'),('مقص','قص'),('ممحاة','محو'),('مذياع','بث'),('هاتف','اتصال'),('حاسبة','حساب'),('ترمومتر','قياس الحرارة'),('ساعة','تحديد الوقت'),('مسمار','تثبيت'),('مجرفة','حفر'),('سماعة','استماع'),
    ],
    'جزء من كل': [
        ('صفحة','كتاب'),('عجلة','سيارة'),('جناح','طائر'),('غرفة','منزل'),('غصن','شجرة'),('إصبع','يد'),('حرف','كلمة'),('خلية','نسيج'),('مقعد','حافلة'),('ضلع','مثلث'),('باب','غرفة'),('سطر','فقرة'),('نغمة','لحن'),('فصل','رواية'),('طالب','فصل'),('دولة','قارة'),('جزيرة','أرخبيل'),('يوم','أسبوع'),('دقيقة','ساعة'),('شعرة','رأس'),('حبة','عنقود'),('لبنة','جدار'),('جذر','نبات'),('ورقة','دفتر'),('زر','قميص'),('عمود','مبنى'),('موجة','بحر'),('سن','فم'),('حجر','طريق'),('قطرة','مطر'),
    ],
    'سبب ونتيجة': [
        ('مطر','نبات'),('احتكاك','حرارة'),('اجتهاد','نجاح'),('إهمال','فشل'),('تدريب','إتقان'),('شمس','تبخر'),('برد','تجمد'),('لقاح','مناعة'),('ري','نمو'),('صيانة','استمرار'),('تلوث','مرض'),('قراءة','معرفة'),('نوم','راحة'),('ضغط','انضغاط'),('نار','دخان'),('زلزال','اهتزاز'),('رياح','أمواج'),('جاذبية','سقوط'),('تمرين','لياقة'),('ادخار','ثروة'),('تنظيم','إنجاز'),('تسرع','خطأ'),('تعاون','نجاح'),('جفاف','تصحر'),('ضوء','رؤية'),('سقي','ازدهار'),('تبريد','تكاثف'),('تعلم','مهارة'),('ازدحام','تأخر'),('إشعال','احتراق'),
    ],
    'وعاء ومحتواه': [
        ('كأس','ماء'),('حقيبة','كتب'),('مكتبة','كتب'),('محفظة','نقود'),('خزان','وقود'),('سلة','فاكهة'),('قارورة','دواء'),('درج','ملابس'),('صندوق','أدوات'),('وعاء','طعام'),('مرآب','سيارة'),('قفص','طائر'),('جراب','هاتف'),('ملف','أوراق'),('مخزن','بضائع'),('حظيرة','ماشية'),('حوض','أسماك'),('ألبوم','صور'),('خلية','عسل'),('مقلمة','أقلام'),('غلاف','رسالة'),('برطمان','عسل'),('حافظة','مستندات'),('كيس','حبوب'),('علبة','مناديل'),('ثلاجة','طعام'),('خزانة','ملابس'),('مكتبة رقمية','ملفات'),('طبق','طعام'),('سفينة','حمولة'),
    ],
    'مكان ورواده': [
        ('مدرسة','طلاب'),('مستشفى','مرضى'),('ملعب','لاعبون'),('محكمة','قضاة'),('مصنع','عمال'),('مزرعة','مزارعون'),('ميناء','سفن'),('مطار','طائرات'),('مكتبة','قراء'),('مسرح','ممثلون'),('عيادة','مرضى'),('مختبر','باحثون'),('ثكنة','جنود'),('جامعة','طلاب'),('مطعم','زبائن'),('فندق','نزلاء'),('مرصد','فلكيون'),('ورشة','فنيون'),('متجر','متسوقون'),('مسجد','مصلون'),('قاعة','حضور'),('ملعب','جمهور'),('محطة','مسافرون'),('حديقة','زوار'),('متحف','زوار'),('مركز تدريب','متدربون'),('بنك','عملاء'),('مكتب','موظفون'),('سوق','بائعون'),('مخبز','خبازون'),
    ],
    'منتج ومنتجه': [
        ('نحل','عسل'),('شجرة','ثمار'),('بقرة','حليب'),('دودة القز','حرير'),('طابعة','ورق مطبوع'),('خباز','خبز'),('شاعر','قصيدة'),('نجار','أثاث'),('مزارع','محصول'),('مصنع','منتج'),('رسام','لوحة'),('مؤلف','كتاب'),('نساج','قماش'),('صائغ','حلي'),('صحفي','خبر'),('مبرمج','برنامج'),('مصور','صورة'),('طاه','وجبة'),('نحات','تمثال'),('مترجم','ترجمة'),('ملحن','لحن'),('مخرج','فيلم'),('خزاف','فخار'),('بنّاء','مبنى'),('محرر','مقال'),('مبتكر','اختراع'),('خياط','ثوب'),('مزارع نحل','عسل'),('مطبعة','كتاب'),('مصفاة','وقود'),
    ],
    'تضاد': [
        ('نور','ظلام'),('شجاعة','جبن'),('قرب','بعد'),('ارتفاع','انخفاض'),('سرعة','بطء'),('نجاح','فشل'),('صمت','ضجيج'),('صيف','شتاء'),('لين','صلابة'),('سخاء','بخل'),('بداية','نهاية'),('حضور','غياب'),('ربح','خسارة'),('قبول','رفض'),('وضوح','غموض'),('اتحاد','انقسام'),('بناء','هدم'),('تذكر','نسيان'),('زيادة','نقصان'),('حركة','سكون'),('صدق','كذب'),('هدوء','صخب'),('اتساع','ضيق'),('قوة','ضعف'),('تقدم','تراجع'),('حياة','موت'),('تفاؤل','تشاؤم'),('ظهور','اختفاء'),('اتصال','انقطاع'),('نشاط','خمول'),
    ],
    'مادة ومنتج': [
        ('خشب','أثاث'),('قطن','قماش'),('زجاج','نافذة'),('حديد','جسر'),('طين','فخار'),('ذهب','حلي'),('جلد','حذاء'),('ورق','كتاب'),('صوف','سجاد'),('رخام','تمثال'),('دقيق','خبز'),('حليب','جبن'),('رمل','زجاج'),('نحاس','سلك'),('إسمنت','بناء'),('بلاستيك','عبوة'),('فحم','طاقة'),('قصب','سكر'),('حبوب','طحين'),('نفط','وقود'),('فضة','حلي'),('حرير','ثوب'),('مطاط','إطار'),('حجر','منزل'),('ألمنيوم','علبة'),('صلصال','مجسم'),('حبر','نص'),('شمع','شمعة'),('ورق مقوى','صندوق'),('جلد','حقيبة'),
    ],
    'صفة وموصوف': [
        ('ثلج','برودة'),('عسل','حلاوة'),('ليمون','حموضة'),('فحم','سواد'),('قطن','نعومة'),('حديد','صلابة'),('مرآة','انعكاس'),('شمس','سطوع'),('ملح','ملوحة'),('ريش','خفة'),('صخر','ثقل'),('زجاج','شفافية'),('مطاط','مرونة'),('نار','حرارة'),('ماء','سيولة'),('عطر','رائحة'),('سكر','حلاوة'),('سماء','اتساع'),('نهر','جريان'),('سكين','حدة'),('حرير','نعومة'),('جليد','برودة'),('فلفل','حرارة'),('قمر','ضياء'),('ليل','ظلمة'),('صحراء','جفاف'),('بحر','ملوحة'),('عشب','خضرة'),('معدن','صلابة'),('رياح','حركة'),
    ],
    'تتابع زمني': [
        ('بذرة','نبات'),('سؤال','إجابة'),('فجر','شروق'),('تسجيل','دخول'),('تخطيط','تنفيذ'),('ولادة','نمو'),('دراسة','اختبار'),('طلب','استجابة'),('جمع','تحليل'),('بحث','نتيجة'),('قراءة','تلخيص'),('إعداد','تقديم'),('تدريب','منافسة'),('اكتشاف','تطبيق'),('مقدمة','خاتمة'),('شتاء','ربيع'),('صباح','مساء'),('بداية','منتصف'),('نوم','استيقاظ'),('زرع','حصاد'),('سؤال','حل'),('تعلم','إتقان'),('تسخين','غليان'),('غيم','مطر'),('بناء','سكن'),('إشعار','استجابة'),('رحيل','وصول'),('تجربة','استنتاج'),('مشكلة','حل'),('فكرة','مشروع'),
    ],
    'درجة في المعنى': [
        ('دافئ','حار'),('بارد','متجمد'),('تعب','إنهاك'),('خوف','هلع'),('فرح','ابتهاج'),('حزن','كآبة'),('جوع','مجاعة'),('عطش','ظمأ'),('ضوء','وهج'),('مطر','سيل'),('ريح','عاصفة'),('صوت','ضجيج'),('مشي','ركض'),('ابتسام','ضحك'),('انزعاج','غضب'),('اهتمام','شغف'),('حب','هيام'),('مرض','وباء'),('صعوبة','استحالة'),('ميل','انحدار'),('دفء','حرارة'),('قلق','فزع'),('برد','صقيع'),('رذاذ','مطر'),('سكون','جمود'),('نمو','ازدهار'),('صمت','خرس'),('نقص','ندرة'),('تأخير','تعطيل'),('لمعان','بريق'),
    ],
}


def add_analogies(bank: Bank,n:int=350):
    relation_names=list(RELATIONS)
    flat_other={r:RELATIONS[r] for r in relation_names}
    i=0
    attempts=0
    while i<n and bank.count('قدرات لفظي')<TARGET_VERBAL and attempts<n*30:
        attempts+=1
        rel=relation_names[i%len(relation_names)]
        pairs=RELATIONS[rel]
        p1=pairs[(i*3)%len(pairs)]; p2=pairs[(i*7+5)%len(pairs)]
        if p1==p2: continue
        distract=[]
        for offset in range(1,5):
            r2=relation_names[(relation_names.index(rel)+offset)%len(relation_names)]
            distract.append(RELATIONS[r2][(i*5+offset)%len(RELATIONS[r2])])
        correct=f'{p2[0]} : {p2[1]}'
        ds=[f'{a} : {b}' for a,b in distract[:3]]
        q=f'{p1[0]} : {p1[1]}'
        exp=f'العلاقة هي «{rel}». لذلك الزوج الموافق هو {correct}؛ لأن العلاقة بين كلمتيه من النوع نفسه.'
        ok=bank.add(exam='قدرات لفظي',category='التناظر اللفظي',skill='العلاقات اللفظية',question=q,correct=correct,distractors=ds,explanation=exp,difficulty='متوسط',keywords=['تناظر لفظي',rel],source_pattern=rel,time_sec=45)
        i+=int(ok)


COMPLETION_BASES = [
    ('لا يكفي أن يمتلك {role} معلومات كثيرة، بل ينبغي أن يكون ___ في تحليلها و___ في عرضها.','دقيقًا، واضحًا',['سريعًا، غامضًا','مترددًا، مطولًا','مشتتًا، موجزًا'],'الدقة مطلوبة في التحليل، والوضوح مطلوب في العرض.'),
    ('كلما ازدادت المسؤوليات، أصبح تنظيم الوقت ___ لا أمرًا ___.','ضرورةً، ثانويًا',['عبئًا، مهمًا','خيارًا، أساسيًا','مشكلةً، عاجلًا'],'ازدياد المسؤوليات يجعل التنظيم ضرورة لا أمرًا ثانويًا.'),
    ('يُقاس نجاح {role} بقدرته على ___ المشكلات، لا بمجرد ___ وجودها.','حلّ، وصف',['تجاهل، إثبات','تعقيد، إنكار','نقل، تبرير'],'النجاح يرتبط بالحل الفعلي، لا بالاكتفاء بوصف المشكلة.'),
    ('القراءة المتأنية لا تزيد المعرفة فحسب، بل تُنمّي القدرة على ___ وتقلل من ___.','التحليل، التسرع',['الحفظ، الفهم','النسيان، التركيز','التقليد، السؤال'],'القراءة المتأنية تعزز التحليل وتحد من التسرع.'),
    ('حين يكون الهدف واضحًا، تصبح الخطوات أكثر ___ والجهد أقل ___.','تنظيمًا، تشتتًا',['غموضًا، أثرًا','تعقيدًا، فائدة','بطئًا، دقة'],'وضوح الهدف ينظم الخطوات ويقلل تشتت الجهد.'),
    ('لا تؤدي كثرة الملاحظات إلى تعلم أفضل ما لم تُرتّب وتُراجع بصورة ___.','منهجية',['عشوائية','متقطعة','سطحية'],'الترتيب والمراجعة المنهجية هما ما يحول الملاحظات إلى تعلم.'),
    ('يتطلب القرار الحكيم معلومات كافية ونظرًا ___ في النتائج.','متأنيًا',['عابرًا','متحيزًا','متسرعًا'],'القرار الحكيم يحتاج نظرًا متأنيًا، لا عابرًا أو متسرعًا.'),
    ('من يراجع أخطاءه بصدق يحولها من مصدر للإحباط إلى فرصة لـ ___.','التعلم',['التكرار','الإنكار','التأجيل'],'مراجعة الخطأ تحول التجربة إلى تعلم.'),
    ('الاختلاف في الرأي لا يفسد الحوار إذا صاحبه احترام و___ للحجة.','إنصات',['تجاهل','استهزاء','تعصب'],'الإنصات للحجة يحفظ جودة الحوار.'),
    ('يُظهر الباحث الجيد مرونة في الفرضيات وثباتًا في ___ العلمية.','المنهجية',['النتائج','الانطباعات','التوقعات'],'يمكن تعديل الفرضيات، لكن المنهجية العلمية يجب أن تبقى منضبطة.'),
    ('كل مشروع كبير يبدأ بفكرة، لكنه لا يكتمل إلا بـ ___ منتظم.','عملٍ',['انتظارٍ','تمنٍ','ترددٍ'],'الفكرة تحتاج عملاً منتظمًا حتى تتحول إلى مشروع.'),
    ('الخبرة لا تعني عدم الخطأ، بل تعني سرعة ___ منه.','التعلم',['الهروب','الانزعاج','التبرير'],'الخبرة تظهر في التعلم من الخطأ.'),
    ('حين تتعدد البدائل، تساعد المعايير الواضحة على ___ الأنسب.','اختيار',['إخفاء','تعقيد','إلغاء'],'المعايير الواضحة تسهّل الاختيار.'),
    ('المعلومة التي لا ترتبط بسياق يسهل ___، أما المرتبطة بفكرة فتدوم.','نسيانها',['فهمها','تطبيقها','تذكرها'],'المعلومة المعزولة أكثر عرضة للنسيان.'),
    ('التخطيط المرن يجمع بين وضوح الاتجاه والقدرة على ___ عند الحاجة.','التكيف',['التوقف','التشتت','التراجع'],'المرونة تعني التكيف مع المستجدات.'),
    ('لا تُقاس جودة السؤال بطوله، بل بقدرته على ___ التفكير.','إثارة',['إيقاف','تشتيت','تكرار'],'السؤال الجيد يحفز التفكير.'),
    ('تزداد قيمة المعلومة عندما تكون صحيحة و___ في الوقت نفسه.','مرتبطة بالسياق',['منفصلة','غامضة','مكررة'],'صحة المعلومة وحدها لا تكفي؛ يلزم ارتباطها بالسياق.'),
    ('الهدوء عند الضغط لا يعني غياب القلق، بل القدرة على ___ه.','إدارته',['إخفائه فقط','تضخيمه','الاستسلام له'],'الهدوء يعني إدارة القلق.'),
    ('يصبح النقد بنّاءً عندما يركز على الفكرة ويبتعد عن ___.','الشخصنة',['الدليل','التوضيح','الاقتراح'],'النقد البناء يناقش الفكرة لا الشخص.'),
    ('النجاح المتكرر نتيجة عادات صغيرة ___ أكثر من كونه حدثًا مفاجئًا.','مستمرة',['متقطعة','عشوائية','مؤقتة'],'الاستمرارية في العادات تصنع نتائج متراكمة.'),
    ('لا يمنع الاختصار من الدقة إذا حُذفت الزوائد وحُفظ ___.','المعنى',['الغموض','التكرار','التشويش'],'الاختصار الجيد يحافظ على المعنى.'),
    ('حين تُعرض البيانات بصريًا، يسهل اكتشاف الأنماط و___ بين القيم.','المقارنة',['الفصل','الخلط','الإخفاء'],'العرض البصري يسهل المقارنة.'),
    ('المتعلم الفعّال لا يكتفي بمعرفة الإجابة، بل يبحث عن ___ الذي قاده إليها.','السبب',['الشكل','الوقت','المكان'],'فهم السبب يعزز نقل التعلم إلى أسئلة جديدة.'),
    ('تكون الخطة واقعية عندما تراعي الوقت والموارد و___ المتوقعة.','العقبات',['الأماني','المبالغات','المصادفات فقط'],'الخطة الواقعية تحسب العقبات.'),
    ('التعاون الناجح يوزع الأدوار بوضوح ويجمع الجهود نحو هدف ___.','مشترك',['متعارض','غامض','فردي صرف'],'العمل التعاوني يحتاج هدفًا مشتركًا.'),
    ('الفكرة القوية تصبح أكثر إقناعًا عندما تدعمها أمثلة و___ موثوقة.','أدلة',['شائعات','انطباعات','مبالغات'],'الأدلة الموثوقة تقوي الحجة.'),
    ('إدارة الأولويات تعني تقديم المهم، لا إنجاز كل ما هو ___.','عاجل فقط',['مفيد','مخطط','واضح'],'العاجل ليس دائمًا الأهم.'),
    ('اللغة الدقيقة تقلل سوء الفهم لأنها تحدد المقصود وتمنع ___.','الالتباس',['الفائدة','الترابط','الاختصار'],'الدقة تمنع الالتباس.'),
    ('التجربة الواحدة قد توحي بنتيجة، لكن التكرار يزيدها ___.','موثوقية',['غموضًا','تحيزًا','مصادفة'],'التكرار يزيد موثوقية النتيجة.'),
    ('الطالب الذي يوزع مذاكرته على أيام عدة يتذكر أكثر ممن يعتمد على ___.','الحفظ المكثف في ليلة واحدة',['المراجعة المتباعدة','التدريب المنتظم','الراحة المنظمة'],'التوزيع الزمني أفضل من الحفظ المكثف في ليلة واحدة.'),
]
ROLES=['الباحث','الطالب','الكاتب','المهندس','المعلم','المحلل','القائد','المتدرب','المصمم','المبرمج']


def add_completions(bank: Bank,n:int=300):
    i=0
    attempts=0
    while i<n and bank.count('قدرات لفظي')<TARGET_VERBAL and attempts<n*30:
        attempts+=1
        base=COMPLETION_BASES[i%len(COMPLETION_BASES)]; role=ROLES[(i//len(COMPLETION_BASES))%len(ROLES)]
        q=base[0].format(role=role)
        correct=base[1]; distractors=base[2]; exp=base[3]
        # add harmless contextual variation for uniqueness
        if i>=len(COMPLETION_BASES):
            q=q.replace('،', f'، في المواقف العملية،',1) if i%2==0 else q.replace('لا ', 'غالبًا لا ',1)
        ok=bank.add(exam='قدرات لفظي',category='إكمال الجمل',skill='فهم السياق',question=q,correct=correct,distractors=distractors,explanation=exp,difficulty='متوسط',keywords=['إكمال الجمل','سياق'],time_sec=50)
        i+=int(ok)


CONTEXT_BASES = [
    ('يحرص {who} على جمع البيانات ثم تنظيمها وتحليلها وإهمال النتائج.',['جمع','تنظيم','تحليل','إهمال'],'إهمال','السياق يتحدث عن خطوات العمل الجيد؛ الأنسب بعد التحليل هو عرض النتائج أو تفسيرها، أما إهمالها فيناقض المعنى.'),
    ('يساعد التخطيط الواضح على تحديد الهدف وترتيب الخطوات وزيادة التشتت.',['التخطيط','تحديد','ترتيب','التشتت'],'التشتت','التخطيط يقلل التشتت ولا يزيده.'),
    ('قرأ {who} النص بعناية، وفهم أفكاره، ثم تجاهل السؤال وأجاب بدقة.',['بعناية','فهم','تجاهل','بدقة'],'تجاهل','الإجابة الدقيقة لا تنسجم مع تجاهل السؤال؛ الأنسب قرأ السؤال أو حلله.'),
    ('يتميز الحوار الناجح بالاحترام والإنصات والمقاطعة المستمرة.',['الاحترام','الإنصات','المقاطعة','المستمرة'],'المقاطعة','المقاطعة المستمرة تعيق الحوار الناجح.'),
    ('تحتاج المهارة إلى تدريب منتظم وصبر واستعجال للنتائج.',['تدريب','منتظم','صبر','استعجال'],'استعجال','الاستعجال يناقض الصبر والتدرج اللازمين لاكتساب المهارة.'),
    ('تحافظ الرياضة المعتدلة على النشاط وتحسن اللياقة وتسبب الخمول.',['تحافظ','النشاط','اللياقة','الخمول'],'الخمول','الرياضة المعتدلة تقلل الخمول ولا تسببه.'),
    ('يستند القرار الرشيد إلى معلومات موثوقة وتحليل هادئ وتخمين عشوائي.',['معلومات','موثوقة','تحليل','عشوائي'],'عشوائي','التخمين العشوائي لا ينسجم مع القرار الرشيد.'),
    ('تسهم القراءة في توسيع المعرفة وتنمية الخيال وتضييق الأفق.',['توسيع','المعرفة','الخيال','تضييق'],'تضييق','القراءة توسع الأفق ولا تضيقه.'),
    ('يقلل النوم الكافي من الإرهاق ويحسن التركيز ويزيد التعب.',['النوم','الإرهاق','التركيز','التعب'],'التعب','النوم الكافي يقلل التعب.'),
    ('تنجح المجموعة عندما تتعاون وتتبادل الخبرات وتخفي المعلومات المهمة.',['تتعاون','تتبادل','الخبرات','تخفي'],'تخفي','إخفاء المعلومات المهمة يضعف التعاون.'),
    ('يشرح المعلم الفكرة بأمثلة واضحة ثم يزيدها غموضًا.',['يشرح','أمثلة','واضحة','غموضًا'],'غموضًا','الأمثلة الواضحة تقلل الغموض.'),
    ('ينظم {who} وقته فينجز المهم ويؤجل الأولويات الأساسية.',['ينظم','ينجز','يؤجل','الأساسية'],'يؤجل','تنظيم الوقت يقتضي تقديم الأولويات الأساسية لا تأجيلها.'),
    ('يحافظ الادخار المنتظم على المال ويساعد على تبديده.',['الادخار','المنتظم','يحافظ','تبديده'],'تبديده','الادخار يمنع التبديد.'),
    ('يفحص الباحث الفرضية بالتجربة ثم يرفض كل نتيجة تخالف توقعه.',['يفحص','التجربة','يرفض','توقعه'],'يرفض','الباحث ينبغي أن يقبل النتيجة المدعومة بالدليل ولو خالفت توقعه.'),
    ('تجعل الإشارات الواضحة الطريق أسهل وتزيد احتمالات الضياع.',['الإشارات','الواضحة','أسهل','الضياع'],'الضياع','وضوح الإشارات يقلل الضياع.'),
    ('يختصر الملخص الجيد المعلومات ويحفظ الفكرة ويضاعف الحشو.',['يختصر','يحفظ','الفكرة','الحشو'],'الحشو','الملخص الجيد يقلل الحشو.'),
    ('يستفيد {who} من الخطأ عندما يراجعه ويفهم سببه ويكرره بلا تعديل.',['يستفيد','يراجعه','يفهم','يكرره'],'يكرره','الاستفادة من الخطأ تقتضي تجنبه أو تصحيحه، لا تكراره بلا تعديل.'),
    ('تحمي كلمة المرور القوية الحساب عندما تكون طويلة ومتوقعة للجميع.',['تحمي','القوية','طويلة','متوقعة'],'متوقعة','كلمة المرور القوية ينبغي أن تكون صعبة التوقع.'),
    ('تساعد الخريطة على تحديد المواقع وفهم الاتجاهات وإخفاء المسافات.',['الخريطة','المواقع','الاتجاهات','إخفاء'],'إخفاء','الخريطة توضح المسافات ولا تخفيها.'),
    ('يقلل فحص المصادر من انتشار الشائعات ويزيد قبول الأخبار المجهولة.',['فحص','المصادر','الشائعات','المجهولة'],'المجهولة','فحص المصادر يقلل قبول الأخبار المجهولة.'),
    ('يسهم التشجير في تحسين الهواء وزيادة الظل وتسريع التصحر.',['التشجير','الهواء','الظل','التصحر'],'التصحر','التشجير يحد من التصحر.'),
    ('يتيح العمل الجماعي توزيع المهام وتبادل الأفكار وعزل الخبرات.',['توزيع','تبادل','الأفكار','عزل'],'عزل','العمل الجماعي يدمج الخبرات ولا يعزلها.'),
    ('تساعد المراجعة المتباعدة على تثبيت المعرفة وتسريع النسيان.',['المراجعة','المتباعدة','تثبيت','النسيان'],'النسيان','المراجعة المتباعدة تقلل النسيان.'),
    ('تمنح المقارنة الدقيقة فهمًا أفضل للفروق وتساوي بين الأشياء المختلفة.',['المقارنة','الدقيقة','الفروق','تساوي'],'تساوي','المقارنة الدقيقة تكشف الفروق ولا تلغيها.'),
    ('يؤدي ترتيب الملفات إلى سهولة الوصول إليها وزيادة ضياعها.',['ترتيب','الملفات','الوصول','ضياعها'],'ضياعها','الترتيب يقلل ضياع الملفات.'),
]
WHOS=['الطالب','الباحث','المتعلم','المحلل','الكاتب','المهندس','المعلم','القارئ','المتدرب','الموظف']


def add_context_errors(bank: Bank,n:int=250):
    i=0
    attempts=0
    while i<n and bank.count('قدرات لفظي')<TARGET_VERBAL and attempts<n*30:
        attempts+=1
        base=CONTEXT_BASES[i%len(CONTEXT_BASES)]; who=WHOS[(i//len(CONTEXT_BASES))%len(WHOS)]
        q='حدد الكلمة غير المناسبة سياقيًا: '+base[0].format(who=who)
        if i>=len(CONTEXT_BASES):
            q=q.replace('ثم ', 'بعد ذلك ',1) if i%2==0 else q.replace('يساعد', 'يسهم',1)
        correct=base[2]; ds=[x for x in base[1] if x!=correct][:3]
        ok=bank.add(exam='قدرات لفظي',category='الخطأ السياقي',skill='اكتشاف التناقض السياقي',question=q,correct=correct,distractors=ds,explanation=base[3],difficulty='متوسط',keywords=['خطأ سياقي','تناقض'],time_sec=50)
        i+=int(ok)


ODD_CATEGORIES = {
    'فواكه':['تفاح','برتقال','موز','عنب','كمثرى','خوخ','رمان','بطيخ','فراولة','تين'],
    'خضروات':['خيار','طماطم','جزر','باذنجان','كوسة','بطاطس','فلفل','خس','سبانخ','بصل'],
    'طيور':['صقر','حمامة','عصفور','نسر','ببغاء','غراب','بط','طاووس','هدهد','بومة'],
    'حيوانات بحرية':['حوت','دلفين','قرش','أخطبوط','سردين','تونة','سلحفاة بحرية','فرس البحر','حبار','قنديل البحر'],
    'أدوات كتابة':['قلم','ممحاة','مسطرة','دفتر','مبراة','حبر','ورق','طباشير','لوح','ملصق'],
    'وسائل نقل':['سيارة','قطار','طائرة','سفينة','حافلة','دراجة','مترو','شاحنة','قارب','مروحية'],
    'مهن':['طبيب','مهندس','معلم','نجار','خباز','مزارع','محاسب','ممرض','مترجم','مصمم'],
    'ألوان':['أحمر','أزرق','أخضر','أصفر','بنفسجي','برتقالي','أبيض','أسود','رمادي','بني'],
    'أشكال':['مثلث','مربع','دائرة','مستطيل','معين','خماسي','سداسي','بيضاوي','شبه منحرف','متوازي أضلاع'],
    'أعضاء الجسم':['يد','قدم','عين','أذن','قلب','رئة','كبد','معدة','دماغ','أنف'],
    'مواد دراسية':['رياضيات','فيزياء','كيمياء','أحياء','لغة عربية','تاريخ','جغرافيا','حاسب','فنون','اقتصاد'],
    'أثاث':['كرسي','طاولة','سرير','خزانة','أريكة','مكتب','رف','مرآة','سجادة','مصباح'],
    'أجهزة':['هاتف','حاسوب','طابعة','شاشة','لوحة مفاتيح','فأرة','كاميرا','مذياع','تلفاز','مكبر صوت'],
    'مشروبات':['ماء','حليب','شاي','قهوة','عصير','لبن','كاكاو','ليمونادة','شراب نعناع','ماء فوار'],
    'حبوب':['أرز','قمح','شعير','ذرة','شوفان','عدس','حمص','فول','دخن','سمسم'],
    'معادن':['حديد','نحاس','ذهب','فضة','ألمنيوم','زنك','رصاص','نيكل','قصدير','بلاتين'],
    'مصادر طاقة':['شمس','رياح','ماء','فحم','نفط','غاز','كتلة حيوية','حرارة جوفية','أمواج','هيدروجين'],
    'فصول السنة':['ربيع','صيف','خريف','شتاء'],
    'اتجاهات':['شمال','جنوب','شرق','غرب','شمال شرقي','شمال غربي','جنوب شرقي','جنوب غربي'],
    'وحدات زمن':['ثانية','دقيقة','ساعة','يوم','أسبوع','شهر','سنة','عقد','قرن','ألفية'],
    'مدن سعودية':['الرياض','جدة','مكة','المدينة','الدمام','أبها','تبوك','حائل','جازان','الطائف'],
    'دول عربية':['السعودية','مصر','الأردن','المغرب','تونس','الجزائر','العراق','عمان','الكويت','البحرين'],
    'أجزاء النبات':['جذر','ساق','ورقة','زهرة','ثمرة','بذرة','غصن','برعم','لحاء','شعيرة جذرية'],
    'عمليات حسابية':['جمع','طرح','ضرب','قسمة','تقريب','تقدير','تحليل','تبسيط','مقارنة','ترتيب'],
    'صفات إيجابية':['صدق','أمانة','تعاون','اجتهاد','صبر','تواضع','رحمة','عدل','وفاء','شجاعة'],
    'صفات سلبية':['كذب','خيانة','كسل','غرور','ظلم','بخل','تعصب','تهور','حسد','إهمال'],
    'أماكن تعليم':['مدرسة','جامعة','مكتبة','مختبر','قاعة','فصل','معهد','مركز تدريب','ورشة','مرصد'],
    'أماكن صحية':['مستشفى','عيادة','صيدلية','مختبر','مركز صحي','غرفة عمليات','طوارئ','عناية مركزة','بنك دم','مستوصف'],
    'أدوات مطبخ':['ملعقة','شوكة','سكين','قدر','مقلاة','طبق','كوب','مصفاة','فرن','خلاط'],
    'أدوات هندسية':['مسطرة','فرجار','منقلة','مثلث رسم','شريط قياس','ميزان','قلم رصاص','حاسبة','ورق بياني','ممحاة'],
    'ظواهر جوية':['مطر','ثلج','ضباب','رياح','برق','رعد','إعصار','سحاب','صقيع','برد'],
    'تضاريس':['جبل','وادي','هضبة','سهل','صحراء','تل','ساحل','جزيرة','منخفض','واحة'],
    'مكونات الحاسوب':['معالج','ذاكرة','قرص صلب','شاشة','لوحة مفاتيح','فأرة','بطاقة رسومات','لوحة أم','مزود طاقة','مروحة'],
    'رياضات':['كرة القدم','كرة السلة','السباحة','التنس','الجري','ركوب الدراجات','الطائرة','الرماية','المبارزة','الجمباز'],
    'أدوات قياس':['ميزان','متر','ساعة','ترمومتر','منقلة','فولتميتر','بارومتر','مسطرة','عداد سرعة','بوصلة'],
    'أنواع كتب':['رواية','معجم','موسوعة','ديوان','سيرة','كتاب علمي','أطلس','دليل','مقرر','مجلة'],
    'مصادر معلومات':['كتاب','مقال','موسوعة','مقابلة','تجربة','تقرير','قاعدة بيانات','خريطة','إحصاء','وثيقة'],
    'أجزاء المنزل':['غرفة','مطبخ','مجلس','حمام','ممر','سطح','حديقة','باب','نافذة','شرفة'],
    'مواد بناء':['إسمنت','حديد','طوب','رمل','حصى','خشب','زجاج','رخام','جبس','طلاء'],
    'حواس':['بصر','سمع','شم','ذوق','لمس'],
    'أفعال حركة':['مشى','ركض','قفز','زحف','سبح','طار','دار','صعد','هبط','انطلق'],
    'أصوات':['همس','صراخ','صفير','طنين','زئير','نهيق','مواء','نباح','هدير','خرير'],
    'أجزاء السيارة':['محرك','عجلة','مقود','مكبح','مصباح','مرآة','مقعد','بطارية','ناقل حركة','خزان وقود'],
    'مراحل الدراسة':['ابتدائي','متوسط','ثانوي','جامعي','دراسات عليا'],
    'قيم علمية':['دقة','موضوعية','أمانة','تجريب','تحقق','توثيق','تحليل','استنتاج','مراجعة','تكرار'],
    'أنواع بيانات':['نص','رقم','صورة','صوت','فيديو','جدول','رسم بياني','خريطة','رمز','إشارة'],
    'مكونات جملة':['اسم','فعل','حرف','مبتدأ','خبر','فاعل','مفعول به','صفة','حال','تمييز'],
    'أزمنة':['ماضٍ','حاضر','مستقبل','فجر','صباح','ظهر','عصر','مساء','ليل','منتصف الليل'],
    'مناسبات':['عيد','زواج','تخرج','نجاح','مولود','افتتاح','تكريم','اجتماع','مؤتمر','معرض'],
    'مصادر ماء':['بئر','نهر','عين','بحيرة','مطر','سد','ينبوع','بحر','خزان','قناة'],
    'أعمال فنية':['لوحة','منحوتة','مسرحية','فيلم','قصيدة','رواية','لحن','تصميم','صورة','رقصة'],
}


def add_odd_words(bank: Bank,n:int=250):
    cats=list(ODD_CATEGORIES)
    i=0
    attempts=0
    while i<n and bank.count('قدرات لفظي')<TARGET_VERBAL and attempts<n*30:
        attempts+=1
        cat=cats[i%len(cats)]; other=cats[(i*7+3)%len(cats)]
        if other==cat: continue
        words=ODD_CATEGORIES[cat]
        start=(i*3)%len(words); trio=[words[(start+j)%len(words)] for j in range(3)]
        outsider=ODD_CATEGORIES[other][(i*5)%len(ODD_CATEGORIES[other])]
        if outsider in trio: continue
        q='أوجد المفردة الشاذة: '+ '، '.join(trio+[outsider])
        exp=f'{trio[0]} و{trio[1]} و{trio[2]} تنتمي إلى فئة «{cat}»، بينما {outsider} تنتمي إلى فئة «{other}».'
        ok=bank.add(exam='قدرات لفظي',category='المفردة الشاذة',skill='المعاني والمفردة المختلفة',question=q,correct=outsider,distractors=trio,explanation=exp,difficulty='سهل',keywords=['مفردة شاذة',cat],explanation_mode='none' if i%3 else 'brief',time_sec=40)
        i+=int(ok)


READING_TOPICS = [
 ('المراجعة المتباعدة','توزيع المراجعة على فترات يساعد الدماغ على استرجاع المعلومة أكثر من مرة','الاعتماد على جلسة واحدة طويلة يجعل التعلم عرضة للنسيان','تقسيم المحتوى إلى وحدات صغيرة وجدولة مراجعتها','يثبت التعلم ويصبح الاسترجاع أسرع'),
 ('الطاقة الشمسية','تحول ضوء الشمس إلى كهرباء من دون احتراق مباشر','تتأثر كفاءتها بزاوية الألواح وتراكم الغبار','تنظيف الألواح وتوجيهها جيدًا وتخزين الفائض','تزداد الاستفادة ويقل الاعتماد على الوقود'),
 ('النوم والتعلم','يساعد النوم على تنظيم الذكريات وترسيخ ما تعلمه الإنسان','السهر الطويل يضعف الانتباه في اليوم التالي','الحفاظ على مواعيد نوم منتظمة وتقليل المنبهات مساءً','يتحسن التركيز والاستيعاب'),
 ('القراءة النقدية','تمكّن القارئ من التمييز بين الرأي والدليل','قد تبدو بعض العبارات مقنعة لأنها مؤثرة لغويًا لا لأنها صحيحة','فحص المصدر ومقارنة الادعاء بالأدلة','يصبح الحكم على النص أكثر موضوعية'),
 ('إدارة الوقت','تساعد على توجيه الجهد إلى الأولويات بدل الانشغال بكل مهمة طارئة','قد تزدحم القائمة بمهام قليلة الأثر','ترتيب المهام وفق الأهمية والوقت المطلوب','يزداد الإنجاز ويقل التشتت'),
 ('الماء في المدن','إدارة الماء بكفاءة تحافظ على مورد محدود','التسرب والاستهلاك غير الرشيد يرفعان الفاقد','إصلاح الشبكات واستخدام أدوات ترشيد ومراقبة الاستهلاك','تنخفض الخسائر وتتحسن الاستدامة'),
 ('التشجير الحضري','يوفر الظل ويساعد على تلطيف حرارة الشوارع','اختيار أنواع غير مناسبة قد يزيد استهلاك الماء','زراعة أنواع محلية وتوزيعها وفق احتياج الأحياء','تتحسن البيئة الحضرية بكلفة أقل'),
 ('الأمن الرقمي','يحمي الحسابات والبيانات من الوصول غير المصرح','إعادة استخدام كلمة مرور واحدة يضاعف الخطر','استخدام كلمات فريدة وتفعيل التحقق الثنائي','تقل احتمالات اختراق الحسابات'),
 ('العمل الجماعي','يجمع خبرات متعددة ويسرع إنجاز المهام المعقدة','غموض الأدوار قد يؤدي إلى تكرار الجهد أو ترك مهام','تحديد المسؤوليات ومتابعة التقدم بوضوح','يتكامل العمل وتتحسن النتيجة'),
 ('الخرائط','تحول المكان إلى تمثيل يساعد على فهم المواقع والمسافات','قد يسيء القارئ فهم الخريطة إذا تجاهل المقياس والرموز','قراءة المفتاح ومقياس الرسم والاتجاهات أولًا','تكون الاستنتاجات المكانية أدق'),
 ('التغذية المتوازنة','تمد الجسم بالعناصر التي يحتاجها من مصادر متنوعة','التركيز على نوع واحد لا يغطي كل الاحتياجات','تنويع الوجبات ومراعاة الكميات','تتحسن الطاقة والصحة العامة'),
 ('الرياضة المعتدلة','تقوي القلب والعضلات وتدعم المزاج','الانقطاع الطويل أو الإفراط قد يسبب إصابة أو ضعف الاستمرار','البدء تدريجيًا ووضع برنامج مناسب','تزداد الفائدة ويستمر الالتزام'),
 ('إعادة التدوير','تقلل كمية النفايات وتعيد مواد نافعة إلى دورة الإنتاج','خلط المواد قد يفسد عملية الفرز','فصل الورق والبلاستيك والمعادن من المصدر','ترتفع جودة المواد المعاد تدويرها'),
 ('المتاحف','تحفظ شواهد الماضي وتتيح تعلمًا بصريًا مباشرًا','عرض القطع دون سياق قد يجعلها مجرد أشياء صامتة','إضافة شرح يربط القطعة بزمنها واستخدامها','يفهم الزائر قيمتها التاريخية'),
 ('التجربة العلمية','تختبر الفرضيات بدل الاكتفاء بالتوقع','تغيير أكثر من عامل يجعل معرفة سبب النتيجة صعبة','تثبيت العوامل وتغيير متغير واحد وتكرار القياس','تصبح النتيجة أكثر موثوقية'),
 ('اللغة الواضحة','تنقل الفكرة بأقل احتمال للالتباس','المصطلحات غير المعرّفة والجمل الطويلة تربك القارئ','تعريف المصطلح وتقسيم الفكرة إلى جمل مترابطة','يسهل الفهم وتقل الأخطاء'),
 ('الذكاء الاصطناعي في التعليم','يساعد على تقديم تدريب يناسب مستوى المتعلم','الاعتماد على الإجابة الآلية من دون تحقق قد ينقل خطأ','استخدامه مساعدًا مع مراجعة بشرية ومصادر موثوقة','تتوسع الفائدة مع الحفاظ على الدقة'),
 ('الزراعة الذكية','تستخدم البيانات لتحديد وقت الري وكمية السماد','القياس غير الدقيق قد يؤدي إلى قرارات خاطئة','معايرة الحساسات وربطها بمراقبة ميدانية','تتحسن الإنتاجية ويقل الهدر'),
 ('النقل العام','ينقل أعدادًا كبيرة باستخدام مساحة ووقود أقل لكل راكب','ضعف الربط بين الخطوط يقلل جاذبيته','تنسيق المواعيد وتسهيل الانتقال بين الوسائل','يزداد الاستخدام وتخف الازدحامات'),
 ('الحدائق العامة','توفر مساحة للحركة والراحة والتواصل الاجتماعي','إهمال الصيانة يجعلها أقل أمانًا وجاذبية','توزيع المرافق وصيانتها وإشراك المجتمع','تظل الحديقة مكانًا حيًا ومفيدًا'),
 ('التنوع الحيوي','يزيد قدرة النظام البيئي على التكيف','اختفاء نوع قد يؤثر في أنواع ترتبط به','حماية المواطن الطبيعية والحد من التلوث','يستمر التوازن البيئي'),
 ('الطباعة ثلاثية الأبعاد','تصنع أجسامًا طبقة بعد طبقة وتتيح نماذج مخصصة','اختيار مادة غير مناسبة يضعف المنتج','مواءمة المادة والتصميم مع الاستخدام','تتحسن المتانة والدقة'),
 ('الاستماع الفعال','يساعد على فهم المقصود قبل الرد','الانشغال بإعداد الرد أثناء حديث الآخر يفوّت تفاصيل مهمة','طرح أسئلة توضيحية وتلخيص ما فُهم','يقل سوء الفهم'),
 ('الادخار','يوفر احتياطًا للمستقبل ويخفف أثر النفقات المفاجئة','الهدف الكبير غير المقسم قد يبدو بعيدًا','تحديد مبلغ دوري وأهداف قصيرة','يتحول الادخار إلى عادة قابلة للاستمرار'),
 ('التعلم بالممارسة','يربط المعرفة بإجراء حقيقي ويكشف مواضع الضعف','المشاهدة وحدها قد تعطي شعورًا زائفًا بالإتقان','حل مسائل وتنفيذ مهام ثم تلقي تغذية راجعة','تزداد القدرة على التطبيق'),
 ('المكتبات الرقمية','تتيح الوصول إلى مصادر كثيرة بسرعة','كثرة النتائج قد تجعل العثور على المصدر المناسب صعبًا','استخدام كلمات بحث دقيقة وفلاتر وفحص الموثوقية','يصل القارئ إلى مواد أنسب'),
 ('الهواء النظيف','ضروري لصحة الإنسان والنظم البيئية','انبعاثات النقل والصناعة ترفع الملوثات','تحسين الكفاءة ودعم النقل النظيف ومراقبة الانبعاثات','تنخفض المخاطر الصحية'),
 ('الصحافة العلمية','تنقل نتائج الأبحاث إلى الجمهور بلغة مفهومة','المبالغة في العناوين قد تشوه حدود الدراسة','شرح المنهج والنتيجة والقيود بوضوح','يتكون فهم أدق للبحث'),
 ('المشي في المدن','وسيلة بسيطة للنشاط والتنقل القصير','الأرصفة غير المتصلة تقلل الأمان','إنشاء مسارات مظللة ومتواصلة ومعابر واضحة','يزداد المشي وتتحسن جودة الحياة'),
 ('حفظ التراث','يصون المباني والحرف والقصص التي تشكل ذاكرة المجتمع','التجميد الكامل قد يحول التراث إلى شيء منفصل عن الحياة','توثيقه وتعليمه وإتاحة استخدامات تحترم أصله','يبقى التراث حاضرًا ومتجددًا'),
 ('المراقبة الذاتية','تمكّن المتعلم من معرفة تقدمه بدل الاعتماد على الشعور','قد يبالغ الشخص في تقدير مستواه من دون قياس','تسجيل النتائج ومقارنتها بأهداف واضحة','يصبح التطوير مبنيًا على بيانات'),
 ('الرسوم البيانية','تلخص بيانات كثيرة في شكل يسهل ملاحظته','اختيار مقياس مضلل قد يضخم الفرق','كتابة المحاور والوحدات واستخدام مقياس مناسب','تكون المقارنة عادلة وواضحة'),
 ('البحث في الإنترنت','يسهّل الوصول إلى معلومات متنوعة','ترتيب النتائج لا يعني أن أولها هو الأدق','مقارنة المصادر والتحقق من الكاتب والتاريخ','تتحسن جودة المعلومات المستخدمة'),
 ('الطاقة الريحية','تحول حركة الهواء إلى كهرباء','تغير سرعة الرياح يجعل الإنتاج متذبذبًا','تنويع مصادر الطاقة وربطها بالتخزين والشبكة','تستقر الإمدادات'),
 ('التعلم التعاوني','يجعل المتعلمين يشرحون أفكارهم ويتعلمون من بعضهم','قد يعتمد بعض الأفراد على جهد الآخرين','توزيع أدوار قابلة للقياس ومراجعة مساهمة كل فرد','تتحقق المشاركة العادلة'),
 ('التصميم البسيط','يركز انتباه المستخدم على ما يحتاجه','تكديس العناصر يزيد الحمل الذهني','ترتيب الأولويات وتقليل الزوائد','يصبح الاستخدام أسرع وأسهل'),
 ('التغذية الراجعة','توضح الفجوة بين الأداء الحالي والمطلوب','العبارات العامة لا تعطي خطوة قابلة للتنفيذ','تحديد السلوك وذكر مثال واقتراح تحسين','يعرف المتعلم ماذا يفعل بعد ذلك'),
 ('التنبؤ بالطقس','يجمع قياسات كثيرة لبناء تقدير للحالة المقبلة','الغلاف الجوي متغير ولذلك لا يخلو التنبؤ من احتمال الخطأ','تحديث النماذج باستمرار وبيان درجة الثقة','يستخدم الناس التنبؤ بوعي أكبر'),
 ('الصيانة الوقائية','تعالج المؤشرات المبكرة قبل تحولها إلى عطل كبير','تأجيل الفحص قد يزيد الكلفة ومدة التوقف','وضع جدول فحص وتسجيل الأعطال المتكررة','تطول عمر المعدات'),
 ('إدارة النفايات','تبدأ بتقليل ما يُستهلك ثم إعادة الاستخدام والتدوير','الاعتماد على التخلص فقط لا يعالج أصل المشكلة','تصميم المنتجات لتدوم وفصل المواد','تقل النفايات من المصدر'),
 ('الواقع الافتراضي','يوفر بيئة محاكاة يمكن التدريب فيها بأمان','المحاكاة لا تمثل كل تفاصيل الواقع','دمجها مع تدريب عملي وتقييم واقعي','يستفيد المتعلم دون أن يخلط بين النموذج والواقع'),
 ('الترجمة','تنقل المعنى بين لغتين لا الكلمات منفردة فقط','الترجمة الحرفية قد تفقد السياق','فهم المقصود والثقافة ثم اختيار تعبير مكافئ','يصل النص طبيعيًا ودقيقًا'),
 ('الابتكار','يجمع معرفة موجودة بطريقة تحل مشكلة فعلية','الفكرة الجديدة وحدها لا تكفي إن لم تُختبر','بناء نموذج وتجربته وتحسينه','تتحول الفكرة إلى حل قابل للاستخدام'),
 ('الذاكرة الخارجية','تستخدم القوائم والتقويم لتخفيف العبء عن الذهن','تسجيل كل شيء دون تنظيم يصنع فوضى جديدة','وضع نظام واحد للمواعيد والمهام ومراجعته','يتفرغ الذهن للفهم واتخاذ القرار'),
 ('الاستدامة','توازن بين احتياجات الحاضر وقدرة المستقبل على تلبية احتياجاته','الحل الذي يوفر اليوم ويهدر غدًا ليس مستدامًا','حساب الأثر طويل المدى للموارد والقرارات','تستمر المنفعة عبر الزمن'),
 ('القيادة الهادئة','تحافظ على وضوح القرار في المواقف الضاغطة','التسرع قد ينقل القلق إلى الفريق','جمع المعلومات وتحديد الأولوية والتواصل بوضوح','يتحرك الفريق بثقة أكبر'),
 ('المقارنة العادلة','تستخدم معيارًا واحدًا عند الحكم على بدائل','تغيير المعيار بين البدائل يؤدي إلى نتيجة منحازة','تحديد المعايير قبل التقييم وتطبيقها على الجميع','يصبح القرار أكثر نزاهة'),
 ('الصور التعليمية','توضح العلاقات المكانية التي يصعب وصفها بالكلمات','الصورة المزدحمة قد تخفي الفكرة الأساسية','إزالة الخلفيات الزائدة ووضع تسميات واضحة','يرى المتعلم المعلومة بسرعة'),
 ('الأسئلة الجيدة','تكشف الفهم وتوجه الانتباه إلى الفكرة الأساسية','السؤال الذي يعتمد على الحفظ فقط لا يقيس القدرة على التطبيق','تنويع المواقف وربط السؤال بمفهوم محدد','يظهر مستوى التعلم الحقيقي'),
 ('التخطيط المالي','يربط الدخل بالنفقات والأهداف','إهمال المصروفات الصغيرة قد يكوّن عجزًا كبيرًا','تسجيل الإنفاق ووضع حدود ومراجعتها','تصبح القرارات المالية أوضح'),
]


def add_reading(bank: Bank,n:int=350):
    i=0
    attempts=0
    while i<n and bank.count('قدرات لفظي')<TARGET_VERBAL and attempts<n*30:
        attempts+=1
        topic=READING_TOPICS[(i//7)%len(READING_TOPICS)]
        title,benefit,challenge,solution,result=topic
        passage=f'{benefit}. غير أن {challenge}. ويمكن التعامل مع ذلك من خلال {solution}. وعند تطبيق هذا الأسلوب، {result}.'
        qtype=i%7
        if qtype==0:
            q='ما الفكرة الرئيسة للنص؟'; c=f'أهمية {title} وكيفية زيادة فائدته'; ds=[f'تاريخ {title} بالتفصيل','رفض استخدام الحلول العملية','مقارنة أرقام غير مذكورة']; exp=f'يجمع النص بين فائدة {title} والتحدي المرتبط به والحل المقترح.'
        elif qtype==1:
            q='ما التحدي الذي ذكره النص؟'; c=challenge; ds=[benefit,solution,result]; exp=f'ذكر النص صراحة أن التحدي هو: {challenge}.'
        elif qtype==2:
            q='ما الحل الذي اقترحه النص؟'; c=solution; ds=[challenge,benefit,result]; exp=f'الحل ورد في الجملة الثالثة: {solution}.'
        elif qtype==3:
            q='ما النتيجة المتوقعة عند تطبيق الحل؟'; c=result; ds=[challenge,benefit,solution]; exp=f'الجملة الأخيرة تبين أن النتيجة هي: {result}.'
        elif qtype==4:
            q='أي عنوان أنسب للنص؟'; c=title; ds=['قصة شخصية غير مكتملة','أرقام وإحصاءات تاريخية','مشكلة بلا حل']; exp=f'العنوان الأنسب هو «{title}» لأنه يغطي موضوع الفقرة كلها.'
        elif qtype==5:
            q='يمكن استنتاج أن الكاتب يدعو إلى ماذا؟'; c='الاستفادة من الفكرة مع معالجة جوانب القصور'; ds=['رفض الفكرة تمامًا','تطبيقها دون مراجعة','الاكتفاء بذكر المشكلة']; exp='النص يعرض فائدة وتحديًا ثم حلًا، وهذا يدل على موقف متوازن يدعو إلى الاستخدام الواعي.'
        else:
            q='أي عبارة تتفق مع مضمون النص؟'; c=f'{solution} يساعد على أن {result}'; ds=[f'{challenge} يؤدي دائمًا إلى أفضل نتيجة',f'لا توجد علاقة بين {title} والنتيجة',f'المشكلة أهم من أي حل']; exp='العبارة الصحيحة تربط الحل المذكور بالنتيجة التي نصت عليها الفقرة.'
        ok=bank.add(exam='قدرات لفظي',category='استيعاب المقروء',skill='فهم النص والاستنتاج',question=q+f' [موضوع: {title}]',correct=c,distractors=ds,explanation=exp,difficulty='متوسط',keywords=['استيعاب مقروء',title],passage=passage,time_sec=75)
        i+=int(ok)




# ---------- Deterministic completion generators (avoid collision stalls) ----------

def add_quant_fillers(bank: Bank, n: int = 200):
    added = 0
    for k in range(1, n + 1):
        if bank.count('قدرات كمي') >= TARGET_QUANT:
            break
        kind = k % 4
        if kind == 0:
            x = 10 + k
            a = 2 + (k % 7)
            b = 3 + (k % 11)
            c = a * x + b
            q = f'حل المعادلة: {a}س + {b} = {c}.'
            exp = f'نطرح {b} من الطرفين ثم نقسم على {a}: س = ({c}-{b})/{a} = {x}.'
            ok = bank.add(exam='قدرات كمي', category='الجبر', skill='المعادلات الخطية', question=q, correct=str(x), distractors=[str(x+1),str(x-1),str(c//a)], explanation=exp, difficulty='متوسط')
        elif kind == 1:
            base = 100 + 5*k
            pct = [10,20,25,40][k%4]
            ans = Fraction(base*pct,100)
            if ans.denominator != 1:
                continue
            q = f'في تدريب رقم {k}، ما قيمة {pct}% من {base}؟'
            c = fmt_num(ans)
            exp = f'نحسب {base} × {pct}/100 = {c}.'
            ok = bank.add(exam='قدرات كمي', category='مسائل حسابية', skill='النسبة المئوية', question=q, correct=c, distractors=[fmt_num(ans+5),fmt_num(base-ans),fmt_num(ans-5)], explanation=exp, difficulty='سهل')
        elif kind == 2:
            start = 2 + k
            diff = 2 + (k%8)
            seq = [start + diff*j for j in range(5)]
            nxt = seq[-1] + diff
            q = f'أكمل المتتابعة رقم {k}: {"، ".join(map(str,seq))}، ...'
            exp = f'الفرق الثابت {diff}، لذلك الحد التالي {nxt}.'
            ok = bank.add(exam='قدرات كمي', category='الجبر', skill='المتتابعات والأنماط', question=q, correct=str(nxt), distractors=[str(nxt+diff),str(nxt-1),str(seq[-1]*2)], explanation=exp, difficulty='سهل')
        else:
            w = 4 + (k%15)
            h = 3 + (k%10)
            ans = 2*(w+h)
            q = f'مستطيل طوله {w} سم وعرضه {h} سم. ما محيطه؟ (نموذج {k})'
            exp = f'المحيط = 2 × (الطول + العرض) = 2 × ({w}+{h}) = {ans} سم.'
            ok = bank.add(exam='قدرات كمي', category='الهندسة', skill='المستطيلات والمربعات', question=q, correct=f'{ans} سم', distractors=[f'{w*h} سم',f'{w+h} سم',f'{ans+2} سم'], explanation=exp, difficulty='سهل', close_notes={f'{w*h} سم':'هذا ناتج المساحة، بينما المطلوب المحيط.'})
        added += int(ok)
    return added


def add_analogies(bank: Bank, n: int = 350):
    added = 0
    relation_names = list(RELATIONS)
    for r_index, rel in enumerate(relation_names):
        pairs = RELATIONS[rel]
        for s_index, p1 in enumerate(pairs):
            if added >= n or bank.count('قدرات لفظي') >= TARGET_VERBAL:
                return
            p2 = pairs[(s_index + 7) % len(pairs)]
            if p2 == p1:
                p2 = pairs[(s_index + 1) % len(pairs)]
            distract = []
            for off in (1,2,3):
                r2 = relation_names[(r_index + off) % len(relation_names)]
                pair = RELATIONS[r2][(s_index*3 + off) % len(RELATIONS[r2])]
                distract.append(f'{pair[0]} : {pair[1]}')
            correct = f'{p2[0]} : {p2[1]}'
            exp = f'العلاقة هي «{rel}»، والزوج {correct} يحمل العلاقة نفسها.'
            ok = bank.add(exam='قدرات لفظي', category='التناظر اللفظي', skill='العلاقات اللفظية', question=f'{p1[0]} : {p1[1]}', correct=correct, distractors=distract, explanation=exp, difficulty='متوسط', keywords=['تناظر لفظي',rel], time_sec=45)
            added += int(ok)


def add_completions(bank: Bank, n: int = 300):
    added = 0
    for role in ROLES:
        for b_index, base in enumerate(COMPLETION_BASES):
            if added >= n or bank.count('قدرات لفظي') >= TARGET_VERBAL:
                return
            core = base[0].format(role=role)
            if '{role}' not in base[0]:
                core = f'في عمل {role}، ' + core[0].lower() + core[1:]
            q = core
            ok = bank.add(exam='قدرات لفظي', category='إكمال الجمل', skill='فهم السياق', question=q, correct=base[1], distractors=base[2], explanation=base[3], difficulty='متوسط', keywords=['إكمال الجمل','سياق'], time_sec=50)
            added += int(ok)


def add_context_errors(bank: Bank, n: int = 250):
    added = 0
    for who in WHOS:
        for base in CONTEXT_BASES:
            if added >= n or bank.count('قدرات لفظي') >= TARGET_VERBAL:
                return
            sentence = base[0].format(who=who)
            q = f'في موقف يخص {who}، حدد الكلمة غير المناسبة سياقيًا: {sentence}'
            correct = base[2]
            ds = [x for x in base[1] if x != correct][:3]
            ok = bank.add(exam='قدرات لفظي', category='الخطأ السياقي', skill='اكتشاف التناقض السياقي', question=q, correct=correct, distractors=ds, explanation=base[3], difficulty='متوسط', keywords=['خطأ سياقي','تناقض'], time_sec=50)
            added += int(ok)


def add_odd_words(bank: Bank, n: int = 250):
    added = 0
    cats = list(ODD_CATEGORIES)
    for c_index, cat in enumerate(cats):
        words = ODD_CATEGORIES[cat]
        for variant in range(6):
            if added >= n or bank.count('قدرات لفظي') >= TARGET_VERBAL:
                return
            other = cats[(c_index + 7 + variant) % len(cats)]
            if other == cat:
                continue
            start = (variant*2 + c_index) % len(words)
            trio = [words[(start+j) % len(words)] for j in range(3)]
            outsider = ODD_CATEGORIES[other][(variant*3+c_index) % len(ODD_CATEGORIES[other])]
            if outsider in trio:
                continue
            q = 'أوجد المفردة الشاذة: ' + '، '.join(trio+[outsider])
            exp = f'{trio[0]} و{trio[1]} و{trio[2]} تنتمي إلى «{cat}»، أما {outsider} فتنتمي إلى «{other}».'
            ok = bank.add(exam='قدرات لفظي', category='المفردة الشاذة', skill='المعاني والمفردة المختلفة', question=q, correct=outsider, distractors=trio, explanation=exp, difficulty='سهل', keywords=['مفردة شاذة',cat], explanation_mode='none' if variant%2 else 'brief', time_sec=40)
            added += int(ok)


# ---------- Finalization and QA ----------

def sanitize_existing_images(root: Path) -> int:
    changed=0
    for p in (root/'assets'/'questions').rglob('*.svg'):
        text=p.read_text(encoding='utf-8')
        new=re.sub(r'<rect\s+width="100%"\s+height="100%"[^>]*/>\s*','',text,count=1)
        if new!=text:
            p.write_text(new,encoding='utf-8'); changed+=1
        ET.parse(p)
    return changed


def final_qa(bank: Bank):
    # Keep exactly target counts while preserving order.
    selected=[]; counts=Counter()
    for q in bank.questions:
        exam=q.get('exam')
        limit=TARGET_QUANT if exam=='قدرات كمي' else TARGET_VERBAL if exam=='قدرات لفظي' else 0
        if limit and counts[exam]<limit:
            selected.append(q); counts[exam]+=1
    bank.questions=selected
    bank.id_counts = Counter(q.get('exam','') for q in selected)

    # Reassign stable identifiers and public sequence.
    local=Counter()
    for idx,q in enumerate(bank.questions,1):
        exam=q['exam']; local[exam]+=1
        q['id']=f"{'QDR-Q' if exam=='قدرات كمي' else 'QDR-V'}-{local[exam]:04d}"
        q['public_id']=260000+idx
        q['created_year']=2026
        q['bank']='قدرات موحد'
        q.pop('test_format',None);q.pop('delivery_mode',None)
        # Explanation mode for direct easy questions; visual and close-choice questions retain teaching support.
        notes=q.get('explanation',{}).get('similar_choices',[]) if isinstance(q.get('explanation'),dict) else []
        if q.get('difficulty')=='سهل' and not q.get('image') and not notes and q.get('category') not in ('استيعاب المقروء','الخطأ السياقي'):
            q['explanation_mode']='none'
        # Never refer to a source's numbered rectangle/figure.
        if q.get('image'):
            q['question']=re.sub(r'(?:المستطيل|الشكل المركب|الشكل) رقم\s*\d+','الشكل الموضح',q['question'])
            q['question']=re.sub(r'\s+',' ',q['question']).strip()

    assert counts['قدرات كمي']==TARGET_QUANT,counts
    assert counts['قدرات لفظي']==TARGET_VERBAL,counts
    assert len(bank.questions)==3000
    ids=[q['id'] for q in bank.questions]; pubs=[q['public_id'] for q in bank.questions]
    assert len(ids)==len(set(ids)); assert pubs==list(range(260001,263001))
    texts=[norm_text(q['question']) + (f"|{q.get('image')}" if q.get('image') else '') for q in bank.questions]
    assert len(texts)==len(set(texts)), 'duplicate normalized question keys'
    for q in bank.questions:
        assert len(q['choices'])==4 and len(set(q['choices']))==4
        assert 0<=int(q['correct'])<4
        assert q['choices'][q['correct']]==q['answer']
        if q.get('image'):
            assert (ROOT/q['image']).exists(),q['image']
            assert not re.search(r'(?:المستطيل|الشكل المركب|الشكل) رقم\s*\d+',q['question'])
        assert q.get('explanation_mode') in ('none','brief','full')
        assert isinstance(q.get('explanation'),dict)
        assert q['explanation'].get('summary') is not None


def main():
    seed=json.loads(QUESTIONS_PATH.read_text(encoding='utf-8'))
    bank=Bank(seed)
    sanitize_existing_images(ROOT)

    # Quantitative: add broad coverage until 1500.
    for fn,args in [
        (add_percentage_questions,170),(add_fraction_questions,150),(add_decimal_questions,120),
        (add_ratio_questions,160),(add_divisibility_questions,120),(add_roots_questions,120),
        (add_average_questions,120),(add_speed_questions,150),(add_word_problem_questions,340),
        (add_algebra_questions,430),(add_probability_questions,130),(add_visual_questions,160),
    ]:
        print('START',fn.__name__,bank.count('قدرات كمي'),flush=True)
        fn(bank,args)
        print('DONE',fn.__name__,bank.count('قدرات كمي'),flush=True)
        if bank.count('قدرات كمي')>=TARGET_QUANT: break
    if bank.count('قدرات كمي') < TARGET_QUANT:
        print('START add_quant_fillers', bank.count('قدرات كمي'), flush=True)
        add_quant_fillers(bank, 500)
        print('DONE add_quant_fillers', bank.count('قدرات كمي'), flush=True)

    # Verbal: five canonical sections.
    for fn,n in [(add_analogies,420),(add_completions,360),(add_context_errors,320),(add_odd_words,320),(add_reading,500)]:
        print('START',fn.__name__,bank.count('قدرات لفظي'),flush=True)
        fn(bank,n)
        print('DONE',fn.__name__,bank.count('قدرات لفظي'),flush=True)

    final_qa(bank)
    QUESTIONS_PATH.write_text(json.dumps(bank.questions,ensure_ascii=False,indent=2),encoding='utf-8')

    modes=Counter(q['explanation_mode'] for q in bank.questions)
    categories=Counter(q['category'] for q in bank.questions)
    images=[q for q in bank.questions if q.get('image')]
    close=sum(bool(q.get('explanation',{}).get('similar_choices')) for q in bank.questions)
    report={
        'version':'65.0.0','total':len(bank.questions),'quant':bank.count('قدرات كمي'),'verbal':bank.count('قدرات لفظي'),
        'public_id_start':bank.questions[0]['public_id'],'public_id_end':bank.questions[-1]['public_id'],
        'images':len(images),'transparent_svg_images':sum(str(q.get('image','')).endswith('.svg') for q in images),
        'explanation_modes':dict(modes),'questions_with_close_choice_explanation':close,
        'categories':dict(categories),'source_policy':'skill-pattern reference only; questions, numbers, wording, drawings and explanations are original',
        'fixed_literal_figure_references':True,
    }
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
