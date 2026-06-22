#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / 'data' / 'questions.json'
ASSET_DIR = ROOT / 'assets' / 'questions' / 'generated67'
REPORT_PATH = ROOT / 'docs' / 'reports' / 'SPRINT_67_TAHSILI_BANK_REPORT.json'
RNG = random.Random(670067)
TARGET_PER_SUBJECT = 300
SUBJECTS = ['فيزياء', 'كيمياء', 'رياضيات', 'الأحياء وعلم البيئة']
SOURCE_DOCS = {
    'فيزياء': ['كتاب الفيزياء 2026.pdf'],
    'كيمياء': ['تجميعات الكيمياء 2025.pdf'],
    'رياضيات': ['كتاب الرياضيات 2025.pdf'],
    'الأحياء وعلم البيئة': ['كتاب الأحياء وعلم البيئة 2026.pdf'],
}


def norm(s: str) -> str:
    s = str(s or '').strip().lower()
    s = re.sub(r'[\u064b-\u065f\u0670]', '', s)
    s = s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ة', 'ه').replace('ى', 'ي')
    return re.sub(r'\s+', ' ', s)


def fmt(x: float | int) -> str:
    x = float(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f'{x:.3f}'.rstrip('0').rstrip('.')


def unique_choices(correct: str, distractors: list[str]) -> list[str]:
    out: list[str] = []
    correct = str(correct).strip()
    for d in distractors:
        d = str(d).strip()
        if d and d != correct and d not in out:
            out.append(d)
        if len(out) == 3:
            return out
    # Safe numeric fallbacks; never create a disguised duplicate of the correct answer.
    m = re.fullmatch(r'(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*(.*)', correct, flags=re.I)
    if m:
        value = float(m.group(1))
        suffix = m.group(2).strip()
        step = max(1.0, abs(value) * 0.1)
        for candidate in (value + step, value - step, value * 2, value / 2 if value else 1, value + 2 * step):
            txt = fmt(candidate) + (f' {suffix}' if suffix else '')
            if txt != correct and txt not in out:
                out.append(txt)
            if len(out) == 3:
                return out
    for txt in ('لا يمكن تحديده', 'المعطيات غير كافية', 'جميع ما سبق'):
        if txt != correct and txt not in out:
            out.append(txt)
        if len(out) == 3:
            break
    return out[:3]


def slug(s: str) -> str:
    return re.sub(r'[^\w\u0600-\u06ff]+', '_', str(s)).strip('_')


def mode_for(difficulty: str, image: str = '', similar: dict[str, str] | None = None) -> str:
    if similar:
        return 'full'
    if difficulty == 'سهل' and not image:
        return 'none'
    if difficulty == 'سهل':
        return 'brief'
    return 'full'


def write_svg(name: str, body: str, width: int = 640, height: int = 360) -> str:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / name
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
text{{font-family:"DejaVu Sans",Arial,sans-serif;fill:#153653;font-weight:700}}
.line{{stroke:#1a86b8;stroke-width:6;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.soft{{stroke:#4bbb9e;stroke-width:5;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.guide{{stroke:#8ca7b8;stroke-width:3;fill:none;stroke-dasharray:8 8}}
.fill{{fill:#dff5ee;stroke:#4bbb9e;stroke-width:4}} .fill2{{fill:#e7f1ff;stroke:#1a86b8;stroke-width:4}}
.label{{font-size:24px}} .small{{font-size:18px}} .tiny{{font-size:15px}}
</style>{body}</svg>'''
    path.write_text(svg, encoding='utf-8')
    ET.parse(path)
    return path.relative_to(ROOT).as_posix()


class Bank:
    def __init__(self, questions: list[dict]):
        self.questions = [dict(q) for q in questions if q.get('exam') != 'تحصيلي']
        self.seen = {norm(q.get('question', '')) for q in self.questions}
        self.counts = Counter()

    def count(self, subject: str) -> int:
        return self.counts[subject]

    def add(self, *, subject: str, unit: str, skill: str, question: str, correct: str,
            distractors: list[str], explanation: str, difficulty: str = 'متوسط',
            steps: list[str] | None = None, keywords: list[str] | None = None,
            misconception_id: str = '', similar: dict[str, str] | None = None,
            image: str = '', image_alt: str = '', hint: str = '', trap: str = '',
            source_pages: str = '', diagnostic: bool = False) -> bool:
        if self.count(subject) >= TARGET_PER_SUBJECT:
            return False
        question = re.sub(r'\s+', ' ', question.strip())
        key = norm(question) + ('|' + image if image else '')
        if not key or key in self.seen:
            return False
        self.seen.add(key)
        correct = str(correct)
        ds = unique_choices(correct, [str(x) for x in distractors])
        local_no = self.count(subject) + 1
        correct_index = (len(self.questions) + local_no) % 4
        choices = ds[:]
        choices.insert(correct_index, correct)
        notes = []
        for choice, note in (similar or {}).items():
            if choice in choices:
                notes.append({'choice_index': choices.index(choice), 'choice': choice, 'note': note})
        prefix = {'فيزياء':'PHY','كيمياء':'CHEM','رياضيات':'MATH','الأحياء وعلم البيئة':'BIO'}[subject]
        q = {
            'id': f'TAH-{prefix}-{local_no:04d}',
            'exam': 'تحصيلي',
            'eligible_tracks': ['علمي', 'أدبي'],
            'category': subject,
            'subject': subject,
            'unit': unit,
            'skill': skill,
            'question': question,
            'choices': choices,
            'correct': correct_index,
            'answer': correct,
            'explain': explanation,
            'difficulty': difficulty,
            'time_per_question_sec': 65 if difficulty == 'سهل' else (85 if difficulty == 'متوسط' else 110),
            'diagnostic': diagnostic,
            'keywords': keywords or [subject, unit, skill],
            'concept_id': f'tahsili.{prefix.lower()}.{slug(unit)}.{slug(skill)}',
            'summary_block_id': '',
            'misconception_id': misconception_id,
            'display_variant': 'diagram' if image else 'standard',
            'source_status': 'original_generated_from_curriculum_map',
            'source_documents': SOURCE_DOCS[subject],
            'source_pages': source_pages,
            'source_pattern': skill,
            'copyright_method': 'original_question_new_values_new_wording',
            'editorial_status': 'qa_passed_internal',
            'release_eligible': True,
            'rights_status': 'original',
            'bank': 'تحصيلي موحد',
            'created_year': 2026,
            'explanation_mode': mode_for(difficulty, image=image, similar=similar),
            'explanation': {
                'summary': explanation,
                'steps': steps or [],
                'similar_choices': notes,
            },
        }
        if hint:
            q['hint'] = hint
        if trap:
            q['explanation']['trap'] = trap
        if image:
            q['image'] = image
            q['image_alt'] = image_alt or 'رسم توضيحي للسؤال'
            q['image_caption'] = ''
        self.questions.append(q)
        self.counts[subject] += 1
        return True


# ---------- Fact question engine ----------

def add_fact_variants(bank: Bank, subject: str, facts: list[tuple[str,str,str,list[str],str]], target: int):
    """fact: unit, prompt subject/term, correct description, wrong descriptions, explanation."""
    idx = 0
    attempts = 0
    while bank.count(subject) < target and attempts < target * 20:
        attempts += 1
        unit, term, correct_desc, wrongs, explanation = facts[idx % len(facts)]
        variant = (idx // len(facts)) % 3
        if variant == 0:
            q = f'أي العبارات الآتية تصف {term} وصفًا صحيحًا؟'
            c = correct_desc
            ds = wrongs
        elif variant == 1:
            q = f'المفهوم الذي ينطبق عليه الوصف الآتي: «{correct_desc}» هو:'
            c = term
            other_terms = [f[1] for f in facts if f[0] == unit and f[1] != term]
            ds = (other_terms + [f[1] for f in facts if f[1] != term])[:6]
        else:
            q = f'اختر العبارة الصحيحة المتعلقة بـ {term}.'
            c = correct_desc
            ds = wrongs[::-1]
        ok = bank.add(subject=subject, unit=unit, skill=term, question=q, correct=c,
                      distractors=ds, explanation=explanation, difficulty='سهل' if variant == 0 else 'متوسط',
                      misconception_id=f'{slug(term)}_confusion')
        if ok:
            idx += 1
        else:
            idx += 1


# ---------- Physics ----------

def physics_facts():
    return [
        ('القياس', 'القياس', 'مقارنة كمية مجهولة بكمية معيارية معلومة', ['تحويل الطاقة من صورة لأخرى','تحديد اتجاه القوة فقط','توقع نتيجة التجربة دون اختبار'], 'القياس يعني مقارنة كمية مجهولة بوحدة أو معيار معروف.'),
        ('القياس', 'دقة القياس', 'ترتبط بأصغر تدريج في أداة القياس', ['تزداد كلما زاد هامش الخطأ','لا تتأثر بالأداة','تعني قرب القياس من القيمة الحقيقية فقط'], 'كلما كان أصغر تدريج أصغر أمكن قراءة قيم أدق، بينما الضبط يتعلق بقرب القياس من القيمة الصحيحة.'),
        ('الحركة', 'المسافة', 'طول المسار الفعلي الذي قطعه الجسم', ['التغير المتجه في الموقع','معدل تغير السرعة','الزمن اللازم للحركة'], 'المسافة كمية قياسية تمثل طول المسار ولا تعتمد على الاتجاه.'),
        ('الحركة', 'الإزاحة', 'التغير المتجه من الموقع الابتدائي إلى النهائي', ['طول المسار الفعلي دائمًا','معدل تغير الموقع مع الزمن','مجموع السرعة والزمن'], 'الإزاحة تعتمد على موضعي البداية والنهاية واتجاه الانتقال.'),
        ('الحركة', 'السرعة المتجهة', 'معدل تغير الإزاحة بالنسبة للزمن', ['معدل تغير المسافة دون اتجاه','حاصل ضرب الكتلة في التسارع','معدل تغير القوة'], 'السرعة المتجهة تتضمن المقدار والاتجاه وتساوي الإزاحة على الزمن.'),
        ('الحركة', 'التسارع', 'معدل تغير السرعة المتجهة بالنسبة للزمن', ['معدل تغير الموقع فقط','القوة المؤثرة في وحدة المساحة','الطاقة المختزنة في الجسم'], 'التسارع يقيس مقدار تغير السرعة المتجهة في كل وحدة زمن.'),
        ('القوى', 'قانون نيوتن الأول', 'يبقى الجسم على حالته ما لم تؤثر فيه قوة محصلة', ['القوة تساوي الكتلة في التسارع','لكل فعل رد فعل','الزخم محفوظ في النظام المعزول'], 'القانون الأول يصف القصور الذاتي عندما تكون محصلة القوى صفرًا.'),
        ('القوى', 'قانون نيوتن الثاني', 'محصلة القوة تساوي الكتلة مضروبة في التسارع', ['القوة تساوي الشغل على الزمن','الطاقة لا تفنى ولا تستحدث','لكل فعل رد فعل مساوٍ له'], 'العلاقة F=ma توضح أن التسارع يتناسب طرديًا مع القوة وعكسيًا مع الكتلة.'),
        ('القوى', 'قانون نيوتن الثالث', 'قوتا الفعل ورد الفعل متساويتان مقدارًا ومتعاكستان اتجاهًا', ['القوتان تؤثران في الجسم نفسه','رد الفعل يحدث بعد الفعل بزمن','الفعل أكبر دائمًا من رد الفعل'], 'قوتا الفعل ورد الفعل متزامنتان وتؤثر كل منهما في جسم مختلف.'),
        ('الشغل والطاقة', 'الشغل', 'حاصل ضرب القوة في الإزاحة في اتجاه القوة', ['معدل بذل الطاقة','حاصل ضرب الكتلة في السرعة','الطاقة الناتجة عن الموقع فقط'], 'يحدث شغل عندما تسبب القوة إزاحة وللمركبة في اتجاه الإزاحة أثر.'),
        ('الشغل والطاقة', 'القدرة', 'معدل إنجاز الشغل أو انتقال الطاقة', ['كمية الحركة','القوة في وحدة المساحة','طاقة الوضع فقط'], 'القدرة تساوي الشغل مقسومًا على الزمن.'),
        ('الشغل والطاقة', 'الطاقة الحركية', 'طاقة يمتلكها الجسم بسبب حركته', ['طاقة بسبب موضعه فقط','مقاومة الجسم لتغير الحركة','معدل بذل الشغل'], 'الطاقة الحركية تعتمد على الكتلة ومربع السرعة.'),
        ('الزخم', 'الزخم الخطي', 'حاصل ضرب كتلة الجسم في سرعته المتجهة', ['حاصل ضرب القوة في المسافة','الطاقة على الزمن','الكتلة على الحجم'], 'الزخم كمية متجهة تساوي p=mv.'),
        ('الدوران', 'عزم القوة', 'مقدار قدرة القوة على إحداث دوران', ['مقاومة السائل للجريان','معدل تغير الزخم فقط','نسبة الكتلة إلى الحجم'], 'العزم يعتمد على القوة وذراعها العمودي عن محور الدوران.'),
        ('الجاذبية', 'قوة الجاذبية', 'قوة تجاذب بين أي جسمين لهما كتلة', ['قوة تنافر بين الشحنات المتشابهة','قوة تعتمد على السرعة فقط','قوة لا تتأثر بالمسافة'], 'تتناسب الجاذبية طرديًا مع حاصل ضرب الكتلتين وعكسيًا مع مربع المسافة.'),
        ('الموجات', 'الموجة الميكانيكية', 'تحتاج وسطًا ماديًا للانتقال', ['تنتقل في الفراغ دائمًا','لا تنقل طاقة','سرعتها ثابتة في جميع الأوساط'], 'الصوت مثال موجة ميكانيكية؛ يحتاج وسطًا ماديًا بينما الضوء لا يحتاج.'),
        ('الموجات', 'التردد', 'عدد الاهتزازات الكاملة في الثانية', ['المسافة بين قمتين متتاليتين','أقصى إزاحة عن موضع الاتزان','الزمن الذي تستغرقه نصف اهتزازة'], 'يقاس التردد بالهرتز، ويرتبط بالدور بالعلاقة f=1/T.'),
        ('الصوت', 'شدة الصوت', 'قدرة الموجة الصوتية المارة خلال وحدة المساحة', ['درجة حدة الصوت فقط','سرعة الصوت في الفراغ','عدد الاهتزازات دون زمن'], 'تزداد شدة الصوت عادة بزيادة سعة الموجة.'),
        ('الضوء', 'الانعكاس', 'ارتداد الضوء عن السطح', ['انحرافه عند انتقاله بين وسطين','تحلله إلى ألوان الطيف','اختفاؤه داخل المادة'], 'في الانعكاس تساوي زاوية السقوط زاوية الانعكاس.'),
        ('الضوء', 'الانكسار', 'تغير اتجاه الضوء بسبب تغير سرعته بين وسطين', ['ارتداد الضوء عن السطح نفسه','انتشار الموجة حول الحواف فقط','تداخل موجتين متساويتين'], 'الانكسار يحدث عند انتقال الضوء بين وسطين مختلفين في معامل الانكسار.'),
        ('الكهرباء', 'شدة التيار الكهربائي', 'معدل مرور الشحنة عبر مقطع موصل', ['الطاقة لكل وحدة شحنة','مقاومة الموصل للتيار','القوة بين شحنتين'], 'التيار I=Q/t ويقاس بالأمبير.'),
        ('الكهرباء', 'فرق الجهد', 'الشغل المبذول لنقل وحدة الشحنة', ['كمية الشحنة المارة في الثانية','مقاومة السلك فقط','طاقة الحركة للجسيم'], 'فرق الجهد V=W/Q ويقاس بالفولت.'),
        ('الكهرباء', 'المقاومة الكهربائية', 'ممانعة الموصل لمرور التيار', ['معدل انتقال الشحنة','القدرة المستهلكة فقط','القوة المغناطيسية'], 'وفق قانون أوم R=V/I عندما تثبت درجة الحرارة.'),
        ('المغناطيسية', 'المجال المغناطيسي', 'منطقة تظهر فيها آثار القوة المغناطيسية', ['طاقة حرارية مخزنة','معدل تغير الشحنة','مسار الضوء في العدسة'], 'يمكن تمثيل المجال بخطوط تخرج خارج المغناطيس من الشمالي إلى الجنوبي.'),
        ('الفيزياء الحديثة', 'التأثير الكهروضوئي', 'انبعاث إلكترونات من سطح فلز عند سقوط ضوء بتردد كافٍ', ['تسخين الفلز بسبب المقاومة فقط','انقسام النواة الثقيلة','اتحاد نواتين خفيفتين'], 'لا يحدث الانبعاث إلا إذا تجاوز تردد الضوء تردد العتبة.'),
        ('الفيزياء النووية', 'الانشطار النووي', 'انقسام نواة ثقيلة إلى نواتين أصغر مع انطلاق طاقة', ['اتحاد نواتين خفيفتين','فقد إلكترونات التكافؤ','تحول الطاقة الحركية إلى وضع'], 'الانشطار يختلف عن الاندماج الذي يجمع نواتين خفيفتين.'),
    ]


def add_physics_numeric(bank: Bank, target: int):
    i = 0
    attempts = 0
    while bank.count('فيزياء') < target and attempts < 20000:
        attempts += 1
        kind = i % 10
        if kind == 0:
            v = RNG.choice([4,5,6,8,10,12,15]); t = RNG.choice([3,4,5,6,8]); d=v*t
            bank.add(subject='فيزياء', unit='الحركة', skill='السرعة المنتظمة', question=f'تحرك جسم بسرعة ثابتة مقدارها {v} m/s لمدة {t} s. ما المسافة التي قطعها؟', correct=f'{d} m', distractors=[f'{v+t} m',f'{abs(v-t)} m',f'{d+t} m'], explanation=f'في الحركة المنتظمة: المسافة = السرعة × الزمن = {v} × {t} = {d} m.', difficulty='سهل', steps=[f'd = vt', f'd = {v}×{t} = {d} m'])
        elif kind == 1:
            vi=RNG.choice([0,2,4,6]); a=RNG.choice([2,3,4,5]); t=RNG.choice([2,3,4,5]); vf=vi+a*t
            close=str(a*t)
            bank.add(subject='فيزياء', unit='الحركة', skill='التسارع المنتظم', question=f'جسم سرعته الابتدائية {vi} m/s وتسارعه {a} m/s² لمدة {t} s. ما سرعته النهائية؟', correct=f'{vf} m/s', distractors=[f'{a*t} m/s',f'{vi+a+t} m/s',f'{vi*t} m/s'], explanation=f'نستخدم vf=vi+at، إذن vf={vi}+({a}×{t})={vf} m/s.', difficulty='متوسط', similar={f'{a*t} m/s':'هذا مقدار التغير في السرعة فقط، ويجب إضافة السرعة الابتدائية إليه.'})
        elif kind == 2:
            m=RNG.choice([2,3,4,5,6,8]); a=RNG.choice([2,3,4,5]); f=m*a
            bank.add(subject='فيزياء', unit='القوى', skill='قانون نيوتن الثاني', question=f'إذا كانت كتلة جسم {m} kg وتسارعه {a} m/s²، فما محصلة القوة المؤثرة فيه؟', correct=f'{f} N', distractors=[f'{m+a} N',f'{m/a:.1f} N',f'{f+m} N'], explanation=f'من قانون نيوتن الثاني F=ma={m}×{a}={f} N.', difficulty='سهل')
        elif kind == 3:
            m=RNG.choice([2,4,6,8,10]); v=RNG.choice([3,4,5,6]); ke=0.5*m*v*v
            bank.add(subject='فيزياء', unit='الشغل والطاقة', skill='الطاقة الحركية', question=f'جسم كتلته {m} kg يتحرك بسرعة {v} m/s. ما طاقته الحركية؟', correct=f'{fmt(ke)} J', distractors=[f'{m*v} J',f'{fmt(m*v*v)} J',f'{fmt(0.5*m*v)} J'], explanation=f'KE=½mv²=½×{m}×{v}²={fmt(ke)} J.', difficulty='متوسط', similar={f'{m*v} J':'هذا يساوي الزخم إذا كانت الوحدة kg·m/s، وليس الطاقة الحركية.'})
        elif kind == 4:
            w=RNG.choice([120,180,240,300,360]); t=RNG.choice([3,4,5,6]); p=w/t
            bank.add(subject='فيزياء', unit='الشغل والطاقة', skill='القدرة', question=f'أنجز جهاز شغلاً مقداره {w} J خلال {t} s. ما قدرته؟', correct=f'{fmt(p)} W', distractors=[f'{w*t} W',f'{w-t} W',f'{t/w:.3f} W'], explanation=f'القدرة P=W/t={w}/{t}={fmt(p)} W.', difficulty='سهل')
        elif kind == 5:
            m=RNG.choice([2,3,4,5]); v=RNG.choice([4,6,8,10]); p=m*v
            bank.add(subject='فيزياء', unit='الزخم', skill='الزخم الخطي', question=f'جسم كتلته {m} kg يتحرك بسرعة {v} m/s. ما مقدار زخمه؟', correct=f'{p} kg·m/s', distractors=[f'{m+v} kg·m/s',f'{v/m:.1f} kg·m/s',f'{m*v*v} kg·m/s'], explanation=f'الزخم p=mv={m}×{v}={p} kg·m/s.', difficulty='سهل')
        elif kind == 6:
            f=RNG.choice([10,20,30,40]); d=RNG.choice([2,3,4,5]); work=f*d
            bank.add(subject='فيزياء', unit='الشغل والطاقة', skill='الشغل', question=f'أثرت قوة ثابتة مقدارها {f} N في اتجاه حركة جسم فأزاحته {d} m. ما الشغل المبذول؟', correct=f'{work} J', distractors=[f'{f+d} J',f'{f/d:.1f} J',f'{work+d} J'], explanation=f'لأن القوة في اتجاه الإزاحة: W=Fd={f}×{d}={work} J.', difficulty='سهل')
        elif kind == 7:
            q=RNG.choice([20,30,40,50]); t=RNG.choice([2,4,5,10]); cur=q/t
            bank.add(subject='فيزياء', unit='الكهرباء', skill='شدة التيار', question=f'مرت شحنة مقدارها {q} C خلال موصل في زمن {t} s. ما شدة التيار؟', correct=f'{fmt(cur)} A', distractors=[f'{q*t} A',f'{q-t} A',f'{t/q:.2f} A'], explanation=f'I=Q/t={q}/{t}={fmt(cur)} A.', difficulty='سهل')
        elif kind == 8:
            v=RNG.choice([6,9,12,18,24]); r=RNG.choice([2,3,4,6]); cur=v/r
            bank.add(subject='فيزياء', unit='الكهرباء', skill='قانون أوم', question=f'وصل فرق جهد مقداره {v} V بمقاومة مقدارها {r} Ω. ما شدة التيار؟', correct=f'{fmt(cur)} A', distractors=[f'{v*r} A',f'{v+r} A',f'{r/v:.2f} A'], explanation=f'من قانون أوم I=V/R={v}/{r}={fmt(cur)} A.', difficulty='متوسط', similar={f'{v*r} A':'الضرب يستخدم لحساب القدرة في حالة مناسبة، أما التيار هنا فيساوي الجهد مقسومًا على المقاومة.'})
        else:
            f=RNG.choice([2,4,5,8,10]); T=1/f
            bank.add(subject='فيزياء', unit='الموجات', skill='العلاقة بين التردد والدور', question=f'إذا كان تردد موجة {f} Hz، فما زمنها الدوري؟', correct=f'{fmt(T)} s', distractors=[f'{f} s',f'{fmt(2/f)} s',f'{fmt(f/2)} s'], explanation=f'T=1/f=1/{f}={fmt(T)} s.', difficulty='متوسط')
        i += 1


def add_physics_images(bank: Bank, target: int):
    i = 0
    attempts = 0
    while bank.count('فيزياء') < target and attempts < 20000:
        attempts += 1
        kind=i%4
        if kind==0:
            t=RNG.choice([2,3,4,5]); v=RNG.choice([3,4,5,6]); d=t*v
            body=f'<line class="line" x1="100" y1="300" x2="550" y2="300"/><line class="line" x1="100" y1="300" x2="100" y2="50"/><line class="soft" x1="100" y1="300" x2="500" y2="100"/><text class="label" x="520" y="320">t</text><text class="label" x="45" y="60">v</text><text class="small" x="470" y="95">({t} s, {v} m/s)</text>'
            image=write_svg(f'physics_vt_{i:03d}.svg',body)
            bank.add(subject='فيزياء',unit='الحركة',skill='مساحة منحنى السرعة-الزمن',question='يمثل الشكل حركة بسرعة تزداد خطيًا من الصفر. إذا كانت النقطة النهائية كما في الرسم، فما الإزاحة خلال الزمن الموضح؟',correct=f'{fmt(0.5*t*v)} m',distractors=[f'{d} m',f'{fmt(t+v)} m',f'{fmt(v/t)} m'],explanation=f'الإزاحة تساوي مساحة المثلث تحت منحنى السرعة-الزمن: ½×{t}×{v}={fmt(0.5*t*v)} m.',difficulty='صعب',image=image,image_alt='منحنى سرعة-زمن خطي من الصفر إلى نقطة نهائية')
        elif kind==1:
            body='<circle class="fill2" cx="320" cy="180" r="95"/><path class="line" d="M320 180 L420 180"/><path class="soft" d="M320 180 L320 70"/><text class="label" x="430" y="185">v</text><text class="label" x="300" y="55">F</text><circle cx="320" cy="180" r="9" fill="#153653"/>'
            image=write_svg(f'physics_circle_{i:03d}.svg',body)
            bank.add(subject='فيزياء',unit='الحركة الدائرية',skill='اتجاه القوة المركزية',question='في الشكل يتحرك الجسم لحظيًا باتجاه السرعة v. ما اتجاه القوة المركزية؟',correct='نحو مركز المسار الدائري',distractors=['في اتجاه السرعة المماسية','بعيدًا عن مركز الدائرة','لا توجد قوة'],explanation='القوة المركزية تكون دائمًا باتجاه مركز المسار وتكون عمودية على السرعة المماسية.',difficulty='متوسط',image=image,image_alt='جسم على مسار دائري مع سهم سرعة مماسي وسهم نحو المركز',similar={'في اتجاه السرعة المماسية':'هذا اتجاه السرعة اللحظية، وليس اتجاه القوة المركزية.'})
        elif kind==2:
            r1=RNG.choice([2,3,4]); r2=RNG.choice([4,6,8]); v=12
            body=f'<rect class="fill2" x="80" y="120" width="150" height="100" rx="14"/><rect class="fill" x="410" y="120" width="150" height="100" rx="14"/><text class="label" x="130" y="180">R={r1}Ω</text><text class="label" x="450" y="180">R={r2}Ω</text><line class="line" x1="230" y1="170" x2="410" y2="170"/><text class="label" x="270" y="90">V={v}V</text>'
            image=write_svg(f'physics_resistors_{i:03d}.svg',body)
            req=r1+r2; cur=v/req
            bank.add(subject='فيزياء',unit='الكهرباء',skill='مقاومات على التوالي',question='المقاومتان في الشكل موصولتان على التوالي. ما شدة التيار الكلي؟',correct=f'{fmt(cur)} A',distractors=[f'{fmt(v/(r1*r2/(r1+r2)))} A',f'{req} A',f'{v*req} A'],explanation=f'في التوالي R الكلية={r1}+{r2}={req}Ω، ثم I=V/R={v}/{req}={fmt(cur)}A.',difficulty='صعب',image=image,image_alt='مقاومتان موصولتان على التوالي مع فرق جهد معلوم')
        else:
            body='<line class="line" x1="100" y1="180" x2="540" y2="180"/><line class="guide" x1="320" y1="60" x2="320" y2="300"/><path class="soft" d="M120 100 L320 180 L520 100"/><path class="line" d="M120 260 L320 180 L520 260"/><text class="small" x="155" y="95">i</text><text class="small" x="470" y="95">r</text><text class="small" x="315" y="45">N</text>'
            image=write_svg(f'physics_reflection_{i:03d}.svg',body)
            bank.add(subject='فيزياء',unit='الضوء',skill='قانون الانعكاس',question='أي علاقة صحيحة للزاويتين المقاسوَتين من العمود المقام في الشكل؟',correct='زاوية السقوط تساوي زاوية الانعكاس',distractors=['زاوية السقوط ضعف زاوية الانعكاس','مجموعهما دائمًا 90°','لا توجد علاقة ثابتة'],explanation='ينص قانون الانعكاس على أن زاوية السقوط تساوي زاوية الانعكاس، وتقاسان من العمود المقام على السطح.',difficulty='سهل',image=image,image_alt='شعاع ساقط ومنعكس حول عمود مقام على سطح عاكس')
        i+=1


# ---------- Chemistry ----------

def chemistry_facts():
    return [
        ('مقدمة الكيمياء','الكيمياء التحليلية','فرع يحدد مكونات المادة وكمياتها',['يدرس مركبات الكربون فقط','يدرس التغيرات النووية فقط','يدرس كيمياء الكائنات الحية حصراً'],'الكيمياء التحليلية تهتم بالتعرف على مكونات العينة وقياس كمياتها.'),
        ('مقدمة الكيمياء','الكيمياء العضوية','فرع يدرس غالبًا مركبات الكربون',['يحدد مكونات العينة وكمياتها','يدرس سلوك النواة فقط','يدرس طاقة التفاعل دون تركيب المادة'],'المركبات العضوية ترتكز غالبًا على الكربون والهيدروجين.'),
        ('المادة','العنصر','مادة نقية لا يمكن تحليلها كيميائيًا إلى أبسط',['مزيج متجانس من مواد','اتحاد فيزيائي لمادتين','مركب بنسب متغيرة'],'العنصر يتكون من نوع واحد من الذرات.'),
        ('المادة','المركب','مادة نقية تنتج من اتحاد عنصرين أو أكثر بنسبة ثابتة',['خليط يمكن فصل مكوناته فيزيائيًا','عنصر واحد متعدد النظائر','مادة نسب مكوناتها متغيرة'],'المركب له تركيب كيميائي ثابت ويمكن تحليله كيميائيًا.'),
        ('المادة','المخلوط المتجانس','خليط ذو تركيب موحد في جميع أجزائه',['مادة نقية من عنصر واحد','خليط تظهر مكوناته بوضوح','مركب ذو صيغة ثابتة'],'المحلول مثال لمخلوط متجانس.'),
        ('الذرة','العدد الذري','عدد البروتونات في نواة الذرة',['مجموع البروتونات والنيوترونات','عدد إلكترونات التكافؤ فقط','عدد مستويات الطاقة'],'العدد الذري يميز العنصر ويساوي عدد البروتونات.'),
        ('الذرة','العدد الكتلي','مجموع البروتونات والنيوترونات',['عدد البروتونات فقط','عدد الإلكترونات في الأيون','كتلة مول واحد'],'العدد الكتلي يمثل عدد النيوكليونات في النواة.'),
        ('الذرة','النظائر','ذرات للعنصر نفسه تتساوى في البروتونات وتختلف في النيوترونات',['عناصر مختلفة متساوية الكتلة','أيونات تختلف في عدد الإلكترونات فقط','مركبات لها الصيغة نفسها'],'النظائر لها العدد الذري نفسه وتختلف في العدد الكتلي.'),
        ('الجدول الدوري','الفلزات القلوية','عناصر المجموعة الأولى شديدة النشاط ولها إلكترون تكافؤ واحد',['عناصر المجموعة 17','غازات نبيلة خاملة','عناصر انتقالية جميعها غازات'],'الفلزات القلوية تفقد إلكترون تكافؤ بسهولة.'),
        ('الجدول الدوري','الهالوجينات','عناصر المجموعة 17 ولها سبعة إلكترونات تكافؤ',['عناصر المجموعة الأولى','عناصر المجموعة 18','عناصر لا فلزية بلا إلكترونات تكافؤ'],'الهالوجينات تميل لاكتساب إلكترون لتكمل مستوى التكافؤ.'),
        ('الجدول الدوري','الغازات النبيلة','عناصر المجموعة 18 مستقرة نسبيًا لاكتمال مستوى التكافؤ',['عناصر شديدة النشاط','فلزات تفقد إلكترونًا واحدًا','عناصر جميعها سائلة'],'استقرار الغازات النبيلة مرتبط باكتمال غلافها الخارجي.'),
        ('الروابط','الرابطة الأيونية','تجاذب بين أيونات موجبة وسالبة بعد انتقال إلكترونات',['مشاركة متساوية للإلكترونات دائمًا','تجاذب بين جزيئات غير قطبية فقط','رابطة بين فلزين حصراً'],'تتكون غالبًا بين فلز ولافلز نتيجة انتقال الإلكترونات.'),
        ('الروابط','الرابطة التساهمية','رابطة تنشأ من مشاركة الذرات في إلكترونات',['انتقال كامل للإلكترونات','تجاذب بين أيونات فقط','تجاذب نوى الذرات دون إلكترونات'],'تتكون الرابطة التساهمية غالبًا بين ذرات لافلزية.'),
        ('التفاعلات','قانون حفظ الكتلة','كتلة المتفاعلات تساوي كتلة النواتج في نظام مغلق',['عدد الجزيئات لا يتغير دائمًا','الحجم يظل ثابتًا في كل تفاعل','الطاقة لا تتحول بين صور'],'الذرات يعاد ترتيبها ولا تفنى أثناء التفاعل الكيميائي.'),
        ('التفاعلات','المحفز','مادة تزيد سرعة التفاعل بخفض طاقة التنشيط ولا تستهلك نهائيًا',['تزيد طاقة التنشيط','تغير نواتج التفاعل دائمًا','تزيد حرارة التفاعل نفسها'],'المحفز يوفر مسارًا بديلًا أقل في طاقة التنشيط.'),
        ('المحاليل','المذيب','المكوّن الموجود غالبًا بكمية أكبر ويذيب المذاب',['المادة المترسبة فقط','المكوّن الأقل دائمًا','الأيون الموجب في المحلول'],'في المحلول يتوزع المذاب داخل المذيب.'),
        ('المحاليل','المولارية','عدد مولات المذاب في لتر من المحلول',['كتلة المذاب على كتلة المحلول فقط','حجم المذيب على عدد المولات','عدد الجزيئات في مول واحد'],'M=n/V باللتر.'),
        ('الأحماض والقواعد','الحمض حسب أرهينيوس','مادة تزيد تركيز +H في الماء',['تزيد تركيز -OH','تمنح زوج إلكترونات','لا تتأين في الماء'],'حمض أرهينيوس يعطي أيونات الهيدروجين في المحلول المائي.'),
        ('الأحماض والقواعد','القاعدة حسب أرهينيوس','مادة تزيد تركيز -OH في الماء',['تزيد تركيز +H','تستقبل بروتونًا فقط دون علاقة بالماء','تتكون من لافلز فقط'],'قاعدة أرهينيوس تزيد أيونات الهيدروكسيد في الماء.'),
        ('الحرارة','التفاعل الطارد للحرارة','يطلق طاقة حرارية إلى الوسط المحيط',['يمتص حرارة من الوسط','لا يتغير فيه المحتوى الحراري','تكون طاقة النواتج أعلى دائمًا'],'في التفاعل الطارد تكون طاقة النواتج أقل من طاقة المتفاعلات.'),
        ('الحرارة','التفاعل الماص للحرارة','يمتص طاقة حرارية من الوسط المحيط',['يطلق حرارة إلى الوسط','لا يحتاج طاقة تنشيط','تكون طاقة النواتج أقل دائمًا'],'في التفاعل الماص تكون طاقة النواتج أعلى من طاقة المتفاعلات.'),
        ('الاتزان','الاتزان الكيميائي الديناميكي','تتساوى سرعتا التفاعل الأمامي والعكسي',['تتوقف التفاعلات تمامًا','تتساوى تراكيز جميع المواد بالضرورة','تختفي المتفاعلات كلها'],'عند الاتزان تستمر التفاعلات في الاتجاهين بالمعدل نفسه.'),
        ('الكهروكيمياء','الأكسدة','فقد الإلكترونات أو زيادة عدد التأكسد',['اكتساب الإلكترونات','انخفاض عدد التأكسد','اتحاد المادة بالماء فقط'],'الأكسدة فقد إلكترونات، والاختزال اكتساب إلكترونات.'),
        ('الكهروكيمياء','الاختزال','اكتساب الإلكترونات أو انخفاض عدد التأكسد',['فقد الإلكترونات','زيادة عدد التأكسد','تفكك المركب حراريًا فقط'],'الاختزال يحدث عند اكتساب الإلكترونات.'),
        ('الكيمياء العضوية','الهيدروكربونات','مركبات تتكون من الكربون والهيدروجين فقط',['مركبات تحتوي الأكسجين فقط','أملاح أيونية معدنية','عناصر انتقالية منفردة'],'تصنف الهيدروكربونات إلى مشبعة وغير مشبعة وعطرية.'),
    ]


def add_chem_numeric(bank: Bank, target: int):
    i=0
    attempts=0
    while bank.count('كيمياء')<target and attempts<20000:
        attempts+=1
        kind=i%9
        if kind==0:
            mass=RNG.choice([18,36,44,58.5,90,117]); molar=RNG.choice([18,22,29.25,44,58.5]); n=mass/molar
            if abs(n-round(n,2))>1e-9: pass
            bank.add(subject='كيمياء',unit='الحسابات الكيميائية',skill='عدد المولات',question=f'عينة كتلتها {mass} g وكتلتها المولية {molar} g/mol. كم عدد مولاتها؟',correct=f'{fmt(n)} mol',distractors=[f'{fmt(mass*molar)} mol',f'{fmt(molar/mass)} mol',f'{fmt(mass+molar)} mol'],explanation=f'n=m/M={mass}/{molar}={fmt(n)} mol.',difficulty='سهل')
        elif kind==1:
            n=RNG.choice([0.2,0.5,1,1.5,2]); vol=RNG.choice([0.25,0.5,1,2]); M=n/vol
            bank.add(subject='كيمياء',unit='المحاليل',skill='المولارية',question=f'أذيب {fmt(n)} mol من مذاب لتكوين {fmt(vol)} L من المحلول. ما المولارية؟',correct=f'{fmt(M)} M',distractors=[f'{fmt(n*vol)} M',f'{fmt(vol/n)} M',f'{fmt(n+vol)} M'],explanation=f'M=n/V={fmt(n)}/{fmt(vol)}={fmt(M)} mol/L.',difficulty='متوسط')
        elif kind==2:
            p=RNG.choice([1,1.5,2]); V=RNG.choice([2,3,4,5]); T=RNG.choice([273,300,320]); R=0.082; n=p*V/(R*T)
            bank.add(subject='كيمياء',unit='الغازات',skill='قانون الغاز المثالي',question=f'غاز ضغطه {p} atm وحجمه {V} L عند درجة حرارة {T} K. ما عدد مولاته تقريبًا؟ استخدم R=0.082 L·atm/mol·K.',correct=f'{fmt(n)} mol',distractors=[f'{fmt(p*V*R*T)} mol',f'{fmt(R*T/(p*V))} mol',f'{fmt(p+V)} mol'],explanation=f'n=PV/RT=({p}×{V})/(0.082×{T})≈{fmt(n)} mol.',difficulty='صعب')
        elif kind==3:
            c=RNG.choice([0.01,0.001,0.0001,1e-5]); ph=-math.log10(c)
            bank.add(subject='كيمياء',unit='الأحماض والقواعد',skill='الرقم الهيدروجيني',question=f'إذا كان تركيز +H في محلول يساوي {c:g} M، فما قيمة pH؟',correct=fmt(ph),distractors=[fmt(14-ph),fmt(c),fmt(1/c)],explanation=f'pH=-log[H+]=-log({c:g})={fmt(ph)}.',difficulty='متوسط',similar={fmt(14-ph):'هذه القيمة تمثل pOH عندما يكون مجموع pH وpOH مساويًا 14.'})
        elif kind==4:
            m=RNG.choice([50,100,150,200]); c=RNG.choice([4.18]); dt=RNG.choice([5,10,15,20]); q=m*c*dt
            bank.add(subject='كيمياء',unit='الكيمياء الحرارية',skill='الحرارة النوعية',question=f'سخنت كتلة ماء مقدارها {m} g فارتفعت حرارتها {dt}°C. احسب الحرارة الممتصة إذا كانت الحرارة النوعية 4.18 J/g·°C.',correct=f'{fmt(q)} J',distractors=[f'{fmt(m*c/dt)} J',f'{fmt(m+dt+c)} J',f'{fmt(m*dt)} J'],explanation=f'q=mcΔT={m}×4.18×{dt}={fmt(q)} J.',difficulty='متوسط')
        elif kind==5:
            half=RNG.choice([2,3,4,5]); periods=RNG.choice([2,3,4]); initial=RNG.choice([80,160,320]); remain=initial/(2**periods); time=half*periods
            bank.add(subject='كيمياء',unit='الكيمياء النووية',skill='عمر النصف',question=f'مادة مشعة عمر نصفها {half} سنوات وكتلتها الابتدائية {initial} g. ما الكتلة المتبقية بعد {time} سنوات؟',correct=f'{fmt(remain)} g',distractors=[f'{fmt(initial/periods)} g',f'{fmt(initial-half*periods)} g',f'{fmt(initial/(2*periods))} g'],explanation=f'مرّت {periods} فترات عمر نصف، لذا الكتلة={initial}/2^{periods}={fmt(remain)} g.',difficulty='متوسط')
        elif kind==6:
            v1=RNG.choice([100,200,250]); m1=RNG.choice([1,2,3]); v2=RNG.choice([500,1000]); m2=m1*v1/v2
            bank.add(subject='كيمياء',unit='المحاليل',skill='التخفيف',question=f'ما مولارية محلول حجمه {v2} mL الناتج من تخفيف {v1} mL من محلول مولاريته {m1} M؟',correct=f'{fmt(m2)} M',distractors=[f'{fmt(m1*v2/v1)} M',f'{fmt(m1+m2)} M',f'{fmt(m1*v1)} M'],explanation=f'M1V1=M2V2، إذن M2=({m1}×{v1})/{v2}={fmt(m2)} M.',difficulty='متوسط')
        elif kind==7:
            protons=RNG.choice([6,8,11,12,17,20]); mass=protons+RNG.choice([6,8,10,12,18,20]); neutrons=mass-protons
            bank.add(subject='كيمياء',unit='الذرة',skill='حساب النيوترونات',question=f'ذرة عددها الذري {protons} وعددها الكتلي {mass}. كم عدد النيوترونات؟',correct=str(neutrons),distractors=[str(protons),str(mass),str(protons+mass)],explanation=f'عدد النيوترونات=العدد الكتلي−العدد الذري={mass}−{protons}={neutrons}.',difficulty='سهل')
        else:
            atoms=RNG.choice([1,2,3,4]); mol=RNG.choice([0.5,1,2]); count=atoms*mol*6.02e23
            bank.add(subject='كيمياء',unit='الحسابات الكيميائية',skill='عدد الجسيمات',question=f'كم عدد الذرات في {fmt(mol)} mol من جزيئات يحتوي كل منها على {atoms} ذرات من العنصر المطلوب؟',correct=f'{count:.2e}',distractors=[f'{mol*6.02e23:.2e}',f'{atoms*6.02e23:.2e}',f'{atoms+mol:.2e}'],explanation=f'عدد الذرات={atoms}×{fmt(mol)}×6.02×10²³={count:.2e}.',difficulty='صعب')
        i+=1


def add_chem_images(bank: Bank,target:int):
    i=0
    attempts=0
    while bank.count('كيمياء')<target and attempts<20000:
        attempts+=1
        kind=i%4
        if kind==0:
            body='<circle class="fill2" cx="320" cy="180" r="40"/><circle class="fill" cx="210" cy="180" r="28"/><circle class="fill" cx="430" cy="180" r="28"/><line class="line" x1="250" y1="180" x2="280" y2="180"/><line class="line" x1="360" y1="180" x2="400" y2="180"/><text class="label" x="300" y="188">O</text><text class="label" x="197" y="188">H</text><text class="label" x="417" y="188">H</text>'
            image=write_svg(f'chem_molecule_{i:03d}.svg',body)
            bank.add(subject='كيمياء',unit='الروابط',skill='تركيب جزيء الماء',question='ما نوع الروابط داخل جزيء الماء الموضح؟',correct='روابط تساهمية قطبية',distractors=['روابط أيونية','روابط فلزية','قوى تشتت فقط'],explanation='تشارك ذرتا الهيدروجين والأكسجين بالإلكترونات، لكن الأكسجين أعلى سالبية فتكون الروابط تساهمية قطبية.',difficulty='متوسط',image=image,image_alt='نموذج مبسط لجزيء ماء H-O-H')
        elif kind==1:
            body='<line class="line" x1="80" y1="300" x2="560" y2="300"/><line class="line" x1="80" y1="300" x2="80" y2="50"/><path class="soft" d="M90 250 C220 60 350 60 500 220"/><line class="guide" x1="90" y1="250" x2="500" y2="220"/><text class="small" x="455" y="330">Reaction</text><text class="small" x="30" y="60">E</text><text class="small" x="290" y="75">Ea</text>'
            image=write_svg(f'chem_energy_{i:03d}.svg',body)
            bank.add(subject='كيمياء',unit='الكيمياء الحرارية',skill='منحنى طاقة التفاعل',question='بالاعتماد على الرسم، ماذا يحدث لطاقة التنشيط عند إضافة محفز؟',correct='تنخفض لأن المحفز يوفر مسارًا بديلًا',distractors=['تزداد لأن سرعة التفاعل تزداد','لا تتغير مطلقًا','تساوي طاقة النواتج'],explanation='المحفز يسرّع التفاعل بتوفير مسار ذي طاقة تنشيط أقل، ولا يغير فرق الطاقة بين المتفاعلات والنواتج.',difficulty='متوسط',image=image,image_alt='منحنى طاقة تفاعل مع قمة تمثل طاقة التنشيط',similar={'تزداد لأن سرعة التفاعل تزداد':'زيادة سرعة التفاعل لا تعني زيادة طاقة التنشيط؛ العكس هو الصحيح عند استخدام محفز.'})
        elif kind==2:
            body='<rect class="fill2" x="130" y="90" width="140" height="180" rx="18"/><rect class="fill" x="370" y="90" width="140" height="180" rx="18"/><line class="line" x1="270" y1="130" x2="370" y2="130"/><line class="line" x1="270" y1="230" x2="370" y2="230"/><text class="label" x="185" y="185">Zn</text><text class="label" x="425" y="185">Cu</text><text class="small" x="290" y="65">e−</text>'
            image=write_svg(f'chem_cell_{i:03d}.svg',body)
            bank.add(subject='كيمياء',unit='الكهروكيمياء',skill='الخلية الجلفانية',question='في خلية جلفانية من الزنك والنحاس كما في الشكل، أين تحدث الأكسدة غالبًا؟',correct='عند قطب الزنك',distractors=['عند قطب النحاس','في السلك الخارجي فقط','لا تحدث أكسدة'],explanation='الزنك أكثر قابلية لفقد الإلكترونات، لذا يتأكسد عند المصعد بينما تختزل أيونات النحاس عند المهبط.',difficulty='صعب',image=image,image_alt='خلية جلفانية مبسطة بقطبي زنك ونحاس')
        else:
            body='<rect class="fill2" x="100" y="70" width="440" height="220" rx="20"/><circle cx="180" cy="130" r="18" fill="#1a86b8"/><circle cx="250" cy="210" r="18" fill="#4bbb9e"/><circle cx="330" cy="120" r="18" fill="#1a86b8"/><circle cx="420" cy="220" r="18" fill="#4bbb9e"/><circle cx="485" cy="140" r="18" fill="#1a86b8"/>'
            image=write_svg(f'chem_solution_{i:03d}.svg',body)
            bank.add(subject='كيمياء',unit='المادة',skill='المخلوط المتجانس',question='أي وصف ينطبق على النموذج الجسيمي في الشكل؟',correct='مخلوط متجانس',distractors=['عنصر نقي','مخلوط غير متجانس بطبقتين','مركب مكوّن من جزيئات متطابقة فقط'],explanation='وجود نوعين من الجسيمات موزعين بانتظام في جميع أجزاء الوعاء يدل على مخلوط متجانس.',difficulty='سهل',image=image,image_alt='وعاء يحوي نوعين من الجسيمات موزعين بانتظام')
        i+=1


# ---------- Mathematics ----------

def math_facts():
    return [
        ('المنطق والبرهان','المثال المضاد','مثال واحد يثبت أن التخمين غير صحيح دائمًا',['دليل يثبت صحة العبارة في جميع الحالات','تعريف لمصطلح هندسي','عبارة شرطية صحيحة دائمًا'],'يكفي مثال مضاد واحد لنقض تخمين عام.'),
        ('المنطق والبرهان','العبارة الشرطية','عبارة على صورة إذا كان p فإن q',['عبارة تربط قضيتين بواو فقط','نفي عبارة بسيطة','معادلة جبرية بلا فرض'],'في p→q يكون p الفرض وq النتيجة.'),
        ('الهندسة','متوازي الأضلاع','شكل رباعي كل ضلعين متقابلين فيه متوازيان',['شكل رباعي له ضلعان فقط متساويان','مثلث له ضلعان متطابقان','دائرة لها وتران متوازيان'],'من خواص متوازي الأضلاع أن الأضلاع المتقابلة متطابقة والقطرين ينصف كل منهما الآخر.'),
        ('الهندسة','المعين','متوازي أضلاع جميع أضلاعه متطابقة',['مستطيل جميع زواياه حادة','شبه منحرف له ضلعان متوازيان فقط','دائرة ذات قطرين متعامدين'],'المعين له أربعة أضلاع متطابقة وقطراه متعامدان.'),
        ('الهندسة','المستطيل','متوازي أضلاع زواياه الأربع قائمة',['معين قطراه متعامدان فقط','مثلث قائم الزاوية','شبه منحرف متساوي الساقين'],'قطرا المستطيل متطابقان وينصف كل منهما الآخر.'),
        ('الدائرة','المماس','مستقيم يلتقي الدائرة في نقطة واحدة',['قطعة تصل مركز الدائرة بنقطة عليها','وتر يمر بالمركز','قوس نصف دائري'],'المماس عمودي على نصف القطر عند نقطة التماس.'),
        ('الدوال','الدالة','علاقة تربط كل عنصر من المجال بعنصر واحد فقط من المدى',['علاقة قد تربط عنصر المجال بعدة عناصر','مجموعة أعداد بلا علاقة','معادلة ليس لها متغير'],'شرط الدالة أن يكون لكل مدخل مخرج واحد فقط.'),
        ('الدوال','الدالة العكسية','دالة تعكس أدوار المدخلات والمخرجات لدالة واحد لواحد',['نفي الدالة الأصلية','مشتقة الدالة','قيمة الدالة عند الصفر'],'وجود عكس دالي يتطلب أن تكون الدالة واحدًا لواحد على مجالها.'),
        ('كثيرات الحدود','النظرية الأساسية في الجبر','كثيرة الحدود من الدرجة n لها n جذور مركبة مع التكرار',['لها جذر حقيقي واحد فقط','عدد جذورها أكبر من درجتها دائمًا','لا يمكن أن يكون لها جذور تخيلية'],'تحدد الدرجة عدد الجذور في مجموعة الأعداد المركبة مع احتساب التكرار.'),
        ('الأسس واللوغاريتمات','اللوغاريتم','الأس الذي يرفع إليه الأساس للحصول على العدد',['حاصل ضرب الأساس في العدد','جذر العدد دائمًا','مقلوب العدد'],'log_b(a)=c يعني b^c=a.'),
        ('المتتابعات','المتتابعة الحسابية','متتابعة يكون الفرق بين كل حدين متتاليين ثابتًا',['متتابعة نسبتها الثابتة بين الحدود','متتابعة لا نمط لها','متتابعة حدودها جميعًا متساوية فقط'],'الحد العام للحسابية يعتمد على الحد الأول والفرق المشترك.'),
        ('المتتابعات','المتتابعة الهندسية','متتابعة تكون النسبة بين كل حدين متتاليين ثابتة',['فرقها بين الحدود ثابت','حدودها أعداد أولية فقط','لا تحتوي حدًا أولًا'],'الحد العام للهندسية a_n=a_1 r^(n-1).'),
        ('المثلثات','جيب الزاوية','نسبة الضلع المقابل إلى الوتر في مثلث قائم',['المجاور إلى الوتر','المقابل إلى المجاور','الوتر إلى المقابل'],'sin θ=المقابل/الوتر.'),
        ('المثلثات','جيب التمام','نسبة الضلع المجاور إلى الوتر في مثلث قائم',['المقابل إلى الوتر','المقابل إلى المجاور','الوتر إلى المجاور'],'cos θ=المجاور/الوتر.'),
        ('الإحصاء','الوسط الحسابي','مجموع القيم مقسومًا على عددها',['القيمة الأكثر تكرارًا','القيمة الوسطى بعد الترتيب','الفرق بين أكبر وأصغر قيمة'],'الوسط الحسابي يقيس مركز البيانات باستخدام جميع القيم.'),
        ('الإحصاء','الوسيط','القيمة الوسطى بعد ترتيب البيانات',['القيمة الأكثر تكرارًا','مجموع القيم على عددها','نصف المدى'],'إذا كان عدد القيم زوجيًا فالوسيط متوسط القيمتين الوسطيتين.'),
        ('الاحتمال','الاحتمال النظري','عدد النواتج المرغوبة على عدد النواتج الممكنة المتساوية الفرص',['عدد مرات التجربة فقط','النتائج غير المرغوبة على المرغوبة','مجموع النواتج الممكنة'],'قيمة الاحتمال تقع بين صفر وواحد.'),
        ('المصفوفات','المصفوفة المربعة','مصفوفة عدد صفوفها يساوي عدد أعمدتها',['مصفوفة لها صف واحد فقط','مصفوفة عناصرها أصفار','مصفوفة أعمدتها أكثر دائمًا'],'المحدد يعرف فقط للمصفوفات المربعة.'),
    ]


def add_math_numeric(bank: Bank,target:int):
    i=0
    attempts=0
    while bank.count('رياضيات')<target and attempts<20000:
        attempts+=1
        kind=i%14
        if kind==0:
            a=RNG.choice([2,3,4,5,6]); b=RNG.choice([1,2,3,4]); x=RNG.choice([2,3,4,5]); c=a*x+b
            bank.add(subject='رياضيات',unit='المعادلات',skill='معادلة خطية',question=f'حل المعادلة {a}x + {b} = {c}.',correct=str(x),distractors=[str(c-b),str((c+b)//a),str(x+1)],explanation=f'نطرح {b} من الطرفين فنحصل على {a}x={c-b}، ثم نقسم على {a}: x={x}.',difficulty='سهل')
        elif kind==1:
            a=RNG.choice([1,2,3]); b=RNG.choice([2,3,4]); c=RNG.choice([5,6,7]); x=RNG.choice([2,3,4]); y=RNG.choice([1,2,3]); r=a*x+b*y+c
            bank.add(subject='رياضيات',unit='التعويض',skill='تقييم تعبير جبري',question=f'إذا كان x={x} وy={y}، فما قيمة {a}x + {b}y + {c}؟',correct=str(r),distractors=[str(a+b+c+x+y),str(a*x+b+y+c),str(r-c)],explanation=f'نعوض: {a}×{x}+{b}×{y}+{c}={r}.',difficulty='سهل')
        elif kind==2:
            base=RNG.choice([2,3,4,5]); e1=RNG.choice([2,3,4]); e2=RNG.choice([1,2,3]); e=e1+e2
            bank.add(subject='رياضيات',unit='الأسس',skill='ضرب قوى لها الأساس نفسه',question=f'بسط {base}^{e1} × {base}^{e2}.',correct=f'{base}^{e}',distractors=[f'{base}^{e1*e2}',f'{base*2}^{e}',f'{base}^{abs(e1-e2)}'],explanation=f'عند ضرب قوتين لهما الأساس نفسه نجمع الأسس: {e1}+{e2}={e}.',difficulty='سهل')
        elif kind==3:
            n=RNG.choice([12,18,20,27,32,45,50,72,98]); root=math.sqrt(n)
            sq=max([k*k for k in range(1,int(root)+1) if n%(k*k)==0]); a=int(math.sqrt(sq)); rem=n//sq
            correct=str(a) if rem==1 else f'{a}√{rem}'
            bank.add(subject='رياضيات',unit='الجذور',skill='تبسيط الجذور',question=f'بسط √{n}.',correct=correct,distractors=[f'√{n//2}',f'{a+1}√{rem}',str(int(root))],explanation=f'نكتب {n}={sq}×{rem}، إذن √{n}=√{sq}√{rem}={correct}.',difficulty='متوسط')
        elif kind==4:
            a=RNG.choice([2,3,4,5]); d=RNG.choice([2,3,4,5]); n=RNG.choice([5,6,7,8]); an=a+(n-1)*d
            bank.add(subject='رياضيات',unit='المتتابعات',skill='الحد العام للمتتابعة الحسابية',question=f'متتابعة حسابية حدها الأول {a} وفرقها {d}. ما الحد رقم {n}؟',correct=str(an),distractors=[str(a+n*d),str(a+(n-2)*d),str(a*d*n)],explanation=f'a_n=a_1+(n−1)d={a}+({n}−1)×{d}={an}.',difficulty='متوسط')
        elif kind==5:
            a=RNG.choice([1,2,3]); r=RNG.choice([2,3]); n=RNG.choice([4,5,6]); an=a*(r**(n-1))
            bank.add(subject='رياضيات',unit='المتتابعات',skill='الحد العام للمتتابعة الهندسية',question=f'متتابعة هندسية حدها الأول {a} ونسبتها {r}. ما الحد رقم {n}؟',correct=str(an),distractors=[str(a*r*n),str(a*r**n),str(a+(n-1)*r)],explanation=f'a_n=a_1 r^(n−1)={a}×{r}^{n-1}={an}.',difficulty='متوسط')
        elif kind==6:
            vals=RNG.sample(range(4,21),5); mean=sum(vals)/5
            bank.add(subject='رياضيات',unit='الإحصاء',skill='الوسط الحسابي',question=f'ما الوسط الحسابي للقيم: {"، ".join(map(str,vals))}؟',correct=fmt(mean),distractors=[str(max(vals)-min(vals)),str(sorted(vals)[2]),fmt(sum(vals)/4)],explanation=f'نجمع القيم ({sum(vals)}) ثم نقسم على عددها (5)، فيكون الوسط {fmt(mean)}.',difficulty='سهل',similar={str(sorted(vals)[2]):'هذه القيمة هي الوسيط بعد ترتيب البيانات، وليست الوسط الحسابي.'})
        elif kind==7:
            total=RNG.choice([20,24,30,36]); fav=RNG.choice([5,6,8,10,12]); g=math.gcd(total,fav); c=f'{fav//g}/{total//g}'
            bank.add(subject='رياضيات',unit='الاحتمال',skill='الاحتمال النظري',question=f'صندوق يحتوي {total} كرة متساوية الفرص، منها {fav} حمراء. ما احتمال سحب كرة حمراء؟',correct=c,distractors=[f'{total-fav}/{total}',f'{total}/{fav}',f'{fav}/{total-fav}'],explanation=f'الاحتمال={fav}/{total}، وبالتبسيط يساوي {c}.',difficulty='سهل')
        elif kind==8:
            b=RNG.choice([3,4,5,6,8]); h=RNG.choice([4,5,6,8,10]); area=b*h/2
            bank.add(subject='رياضيات',unit='الهندسة',skill='مساحة المثلث',question=f'مثلث قاعدته {b} cm وارتفاعه {h} cm. ما مساحته؟',correct=f'{fmt(area)} cm²',distractors=[f'{b*h} cm²',f'{b+h} cm²',f'{fmt((b+h)/2)} cm²'],explanation=f'مساحة المثلث=½×القاعدة×الارتفاع=½×{b}×{h}={fmt(area)} cm².',difficulty='سهل')
        elif kind==9:
            r=RNG.choice([2,3,4,5,6]); area=math.pi*r*r
            bank.add(subject='رياضيات',unit='الدائرة',skill='مساحة الدائرة',question=f'دائرة نصف قطرها {r} cm. ما مساحتها بدلالة π؟',correct=f'{r*r}π cm²',distractors=[f'{2*r}π cm²',f'{r}π cm²',f'{2*r*r}π cm²'],explanation=f'A=πr²=π×{r}²={r*r}π cm².',difficulty='سهل',similar={f'{2*r}π cm²':'هذه صيغة محيط الدائرة 2πr، وليست المساحة.'})
        elif kind==10:
            x1,y1=RNG.choice([(1,2),(2,3),(3,1)]); x2,y2=RNG.choice([(5,6),(6,3),(3,7)]); mx=(x1+x2)/2; my=(y1+y2)/2
            bank.add(subject='رياضيات',unit='الهندسة التحليلية',skill='نقطة المنتصف',question=f'ما نقطة منتصف القطعة الواصلة بين ({x1}،{y1}) و({x2}،{y2})؟',correct=f'({fmt(mx)}،{fmt(my)})',distractors=[f'({x1+x2}،{y1+y2})',f'({fmt((x2-x1)/2)}،{fmt((y2-y1)/2)})',f'({x1}،{y2})'],explanation=f'نقطة المنتصف=((x1+x2)/2،(y1+y2)/2)=({fmt(mx)}،{fmt(my)}).',difficulty='متوسط')
        elif kind==11:
            base=RNG.choice([2,3,5,10]); exp=RNG.choice([2,3,4]); val=base**exp
            bank.add(subject='رياضيات',unit='اللوغاريتمات',skill='تعريف اللوغاريتم',question=f'ما قيمة log_{base}({val})؟',correct=str(exp),distractors=[str(base*exp),str(val/base),str(exp+1)],explanation=f'لأن {base}^{exp}={val}، فإن log_{base}({val})={exp}.',difficulty='سهل')
        elif kind==12:
            a=RNG.choice([1,2,3,4]); b=RNG.choice([2,3,4,5]); det=a*b-1
            bank.add(subject='رياضيات',unit='المصفوفات',skill='محدد مصفوفة 2×2',question=f'ما محدد المصفوفة [[{a},1],[1,{b}]]؟',correct=str(det),distractors=[str(a*b+1),str(a+b),str(a-b)],explanation=f'المحدد=ad−bc=({a}×{b})−(1×1)={det}.',difficulty='متوسط')
        else:
            opp=RNG.choice([3,4,5,6,8]); hyp=RNG.choice([10,12,15,20]); ratio=opp/hyp
            bank.add(subject='رياضيات',unit='المثلثات',skill='جيب الزاوية',question=f'في مثلث قائم، طول الضلع المقابل للزاوية θ هو {opp} والوتر {hyp}. ما sin θ؟',correct=fmt(ratio),distractors=[fmt(hyp/opp),fmt((hyp-opp)/hyp),fmt(opp/(hyp-opp))],explanation=f'sin θ=المقابل/الوتر={opp}/{hyp}={fmt(ratio)}.',difficulty='متوسط')
        i+=1


def add_math_images(bank: Bank,target:int):
    i=0
    attempts=0
    while bank.count('رياضيات')<target and attempts<20000:
        attempts+=1
        kind=i%4
        if kind==0:
            b=RNG.choice([6,8,10]); h=RNG.choice([4,5,6]); area=b*h/2
            body=f'<polygon class="fill2" points="100,280 540,280 360,70"/><line class="guide" x1="360" y1="70" x2="360" y2="280"/><text class="label" x="285" y="330">{b} cm</text><text class="label" x="375" y="180">{h} cm</text>'
            image=write_svg(f'math_triangle_{i:03d}.svg',body)
            bank.add(subject='رياضيات',unit='الهندسة',skill='مساحة المثلث',question='ما مساحة المثلث الموضح في الشكل؟',correct=f'{fmt(area)} cm²',distractors=[f'{b*h} cm²',f'{b+h} cm²',f'{fmt((b+h)/2)} cm²'],explanation=f'المساحة=½×{b}×{h}={fmt(area)} cm².',difficulty='سهل',image=image,image_alt='مثلث موضح عليه طول القاعدة والارتفاع')
        elif kind==1:
            r=RNG.choice([3,4,5,6]); body=f'<circle class="fill2" cx="320" cy="180" r="110"/><line class="line" x1="320" y1="180" x2="430" y2="180"/><text class="label" x="350" y="165">r={r}</text>'
            image=write_svg(f'math_circle_{i:03d}.svg',body)
            bank.add(subject='رياضيات',unit='الدائرة',skill='محيط الدائرة',question='ما محيط الدائرة الموضحة بدلالة π؟',correct=f'{2*r}π',distractors=[f'{r*r}π',f'{r}π',f'{4*r}π'],explanation=f'C=2πr=2π×{r}={2*r}π.',difficulty='سهل',image=image,image_alt='دائرة موضح عليها نصف القطر',similar={f'{r*r}π':'هذه صيغة مساحة الدائرة πr²، وليست المحيط.'})
        elif kind==2:
            body='<line class="line" x1="90" y1="300" x2="560" y2="300"/><line class="line" x1="90" y1="300" x2="90" y2="50"/><path class="soft" d="M100 270 L220 210 L350 150 L500 80"/><text class="small" x="505" y="325">x</text><text class="small" x="50" y="55">y</text>'
            image=write_svg(f'math_line_{i:03d}.svg',body)
            bank.add(subject='رياضيات',unit='الدوال',skill='ميل المستقيم',question='ما إشارة ميل المستقيم في الرسم؟',correct='موجب',distractors=['سالب','صفر','غير معرف'],explanation='يرتفع المستقيم من اليسار إلى اليمين، لذلك ميله موجب.',difficulty='سهل',image=image,image_alt='مستقيم متزايد على محورين')
        else:
            a=RNG.choice([3,4,5]); b=RNG.choice([4,5,12]); c=math.sqrt(a*a+b*b)
            body=f'<polygon class="fill2" points="130,280 500,280 130,70"/><rect x="130" y="250" width="30" height="30" fill="none" stroke="#153653" stroke-width="4"/><text class="label" x="280" y="330">{b}</text><text class="label" x="85" y="180">{a}</text><text class="label" x="330" y="160">?</text>'
            image=write_svg(f'math_right_triangle_{i:03d}.svg',body)
            bank.add(subject='رياضيات',unit='الهندسة',skill='نظرية فيثاغورس',question='ما طول الوتر في المثلث القائم الموضح؟',correct=fmt(c),distractors=[str(a+b),fmt(abs(b-a)),fmt(a*a+b*b)],explanation=f'c=√({a}²+{b}²)=√({a*a+b*b})={fmt(c)}.',difficulty='متوسط',image=image,image_alt='مثلث قائم موضح عليه طولا الضلعين القائمين')
        i+=1


# ---------- Biology and ecology ----------

def bio_facts():
    return [
        ('التصنيف','النوع','مجموعة مخلوقات تستطيع التزاوج وإنتاج نسل خصب',['مجموعة تضم عدة أجناس','أعلى مستوى تصنيفي','مجموعة كائنات في موطن واحد دون تكاثر'],'النوع هو الوحدة الأساسية في التصنيف ويضم أفرادًا متشابهين قادرين على إنتاج نسل خصب.'),
        ('التصنيف','التسمية الثنائية','اسم علمي يتكون من اسم الجنس واسم النوع',['اسم الشعبة والطائفة','اسم المملكة فقط','وصف سلوكي للكائن'],'توحّد التسمية الثنائية أسماء المخلوقات عالميًا.'),
        ('الفيروسات','الفيروس','مادة وراثية محاطة بغلاف بروتيني ولا يتكاثر منفردًا',['خلية بدائية النواة كاملة','كائن ذاتي التغذي','فطر وحيد الخلية'],'الفيروس يحتاج خلية مضيفة لإنتاج نسخ جديدة منه.'),
        ('البكتيريا','البكتيريا','مخلوقات وحيدة الخلية بدائية النواة',['حقيقية النواة متعددة الخلايا دائمًا','لا تحتوي مادة وراثية','فيروسات ذات جدار خلوي'],'البكتيريا لا تمتلك نواة محاطة بغشاء.'),
        ('الطلائعيات','الطلائعيات','حقيقية النواة ومعظمها وحيد الخلية',['بدائية النواة جميعها','حيوانات متعددة الخلايا فقط','فيروسات لا خلوية'],'تضم الطلائعيات مجموعات شبيهة بالحيوانات والنباتات والفطريات.'),
        ('الفطريات','الفطريات','حقيقية النواة غير ذاتية التغذي وتمتص غذاءها',['تصنع غذاءها بالبناء الضوئي دائمًا','بدائية النواة','تبتلع الغذاء كالحيوانات فقط'],'للفطريات جدر خلوية كيتينية وتتغذى بالامتصاص.'),
        ('النباتات','البناء الضوئي','تحويل الطاقة الضوئية إلى طاقة كيميائية في الجلوكوز',['تفكيك الجلوكوز لإنتاج ATP فقط','انتقال الماء عبر الخشب','خروج بخار الماء من الثغور'],'يحدث البناء الضوئي أساسًا في البلاستيدات الخضراء.'),
        ('النباتات','الخشب','نسيج ينقل الماء والأملاح من الجذور إلى أعلى النبات',['ينقل السكريات من الأوراق','يحمي البذرة','ينظم فتح الثغور'],'الخشب مسؤول أساسًا عن نقل الماء والأملاح.'),
        ('النباتات','اللحاء','نسيج ينقل السكريات والمواد العضوية في النبات',['ينقل الماء فقط صعودًا','ينتج حبوب اللقاح','يكون غلاف البذرة'],'اللحاء يوزع نواتج البناء الضوئي إلى أجزاء النبات.'),
        ('الحيوانات','الحبل الظهري','دعامة مرنة تمتد على طول الجسم في الحبليات خلال مرحلة من حياتها',['قناة هضمية خارجية','جدار خلوي كيتيني','عضو تنفسي في النباتات'],'الحبل الظهري من الصفات الأساسية للحبليات.'),
        ('الخلية','الغشاء البلازمي','ينظم مرور المواد من الخلية وإليها',['يحمل المعلومات الوراثية','يصنع البروتين مباشرة','ينتج الطاقة الضوئية'],'الغشاء ذو نفاذية اختيارية ويحافظ على الاتزان الداخلي.'),
        ('الخلية','النواة','تحتوي معظم المادة الوراثية في الخلية حقيقية النواة',['موقع إنتاج ATP فقط','موقع تصنيع الدهون فقط','تركيب موجود في البكتيريا محاط بغشاء'],'النواة تتحكم في كثير من أنشطة الخلية لاحتوائها DNA.'),
        ('الخلية','الميتوكندريا','موقع رئيس لإنتاج ATP بالتنفس الخلوي',['موقع بناء البروتين','موقع تخزين الماء في النبات فقط','موقع تصنيع DNA النووي'],'الميتوكندريا تحول طاقة الغذاء إلى ATP.'),
        ('الخلية','الريبوسومات','تراكيب تصنع البروتين',['تنتج ATP','تهضم الجسيمات','تخزن الماء والأملاح'],'تترجم الريبوسومات المعلومات الموجودة في mRNA إلى بروتين.'),
        ('الخلية','الانتشار','انتقال الجزيئات من تركيز مرتفع إلى منخفض',['انتقال الماء فقط عبر غشاء','نقل يحتاج ATP عكس التدرج','ابتلاع الخلية لجسيم كبير'],'الانتشار نقل سلبي لا يحتاج طاقة مباشرة.'),
        ('الخلية','الأسموزية','انتقال الماء عبر غشاء شبه منفذ من تركيز ماء أعلى إلى أقل',['انتقال الأيونات عكس التدرج','انقسام الخلية','تفكيك الجلوكوز'],'الأسموزية نوع خاص من الانتشار يتعلق بالماء.'),
        ('الانقسام','الانقسام المتساوي','ينتج خليتين متماثلتين وراثيًا غالبًا',['ينتج أربع خلايا أحادية المجموعة','يخفض عدد الكروموسومات للنصف','يحدث فقط في الخلايا الجنسية'],'يساعد الانقسام المتساوي في النمو والتعويض.'),
        ('الانقسام','الانقسام المنصف','ينتج خلايا جنسية بنصف عدد الكروموسومات',['ينتج خليتين متماثلتين','يحافظ على العدد الثنائي في الأمشاج','لا يسبب تنوعًا وراثيًا'],'الانقسام المنصف يكوّن الأمشاج ويسهم في التنوع الوراثي.'),
        ('الوراثة','الجين','جزء من DNA يحمل معلومات لصفة أو منتج وظيفي',['كروموسوم كامل دائمًا','عضية خلوية','بروتين بلا شفرة'],'الجينات وحدات وراثية تقع على الكروموسومات.'),
        ('الوراثة','الصفة السائدة','صفة تظهر عند وجود أليل سائد واحد على الأقل',['لا تظهر إلا عند وجود أليلين متنحيين','تختفي دائمًا في الجيل الأول','تعني أن الأليل أكثر انتشارًا بالضرورة'],'السائد يعبّر عنه في النمط الظاهري حتى في الحالة غير المتماثلة.'),
        ('الوراثة','الطراز الجيني','تركيب الأليلات التي يحملها الفرد لصفة',['المظهر الخارجي للصفة','مكان الجين على الكروموسوم','عدد الكروموسومات فقط'],'الطراز الجيني مثل Aa، أما الطراز الظاهري فهو الصفة الملاحظة.'),
        ('الوراثة','DNA','جزيء يحمل المعلومات الوراثية في الخلايا',['سكر بسيط لإنتاج الطاقة','دهون غشائية','هرمون بروتيني'],'يتكون DNA من نيوكليوتيدات ويحمل شفرة بناء البروتينات.'),
        ('جسم الإنسان','القلب','عضو عضلي يضخ الدم عبر الأوعية',['ينتج خلايا الدم الحمراء','يرشح الفضلات من الدم','يهضم البروتينات'],'القلب يحافظ على دوران الدم في الرئتين وبقية الجسم.'),
        ('جسم الإنسان','الحويصلات الهوائية','موقع تبادل الغازات في الرئتين',['موقع إنتاج خلايا الدم','صمامات في القلب','أنابيب تنقل البول'],'جدر الحويصلات رقيقة ومحاطة بشعيرات لتسهيل الانتشار.'),
        ('جسم الإنسان','النيفرون','الوحدة الوظيفية في الكلية',['وحدة بناء العضلة','وحدة تبادل الغازات','خلية عصبية'],'يرشح النفرون الدم ويسهم في تكوين البول وضبط الماء والأملاح.'),
        ('جسم الإنسان','الإنسولين','هرمون يساعد على خفض سكر الدم',['يرفع سكر الدم دائمًا','يزيد ضربات القلب فقط','ينتج من الغدة الدرقية'],'يفرز الإنسولين من البنكرياس ويساعد الخلايا على أخذ الجلوكوز.'),
        ('المناعة','الأجسام المضادة','بروتينات ترتبط بمولدات ضد محددة',['خلايا تنقل الأكسجين','إنزيمات هضم','هرمونات نمو'],'تنتج الخلايا البائية أجسامًا مضادة نوعية.'),
        ('البيئة','الجماعة الحيوية','أفراد النوع نفسه الذين يعيشون في منطقة واحدة',['جميع الأنواع في منطقة','العوامل الحية وغير الحية','المحيط الحيوي كله'],'الجماعة تتكون من أفراد النوع نفسه ضمن مكان وزمن محددين.'),
        ('البيئة','المجتمع الحيوي','جميع الجماعات الحيوية المختلفة في منطقة',['أفراد نوع واحد','العوامل غير الحية فقط','موطن كائن واحد'],'المجتمع يشمل أنواعًا متعددة تتفاعل معًا.'),
        ('البيئة','النظام البيئي','المجتمع الحيوي مع العوامل غير الحية المحيطة',['جماعة من نوع واحد','منطقة مناخية واسعة فقط','سلسلة غذائية منفردة'],'النظام البيئي يدمج الكائنات مع الماء والهواء والتربة وغيرها.'),
        ('البيئة','المنتجات','مخلوقات تصنع غذاءها وتبدأ معظم السلاسل الغذائية',['مستهلكات أولية فقط','محللات','مفترسات عليا'],'النباتات والطحالب منتجات تحول الطاقة إلى مادة عضوية.'),
        ('البيئة','المحللات','مخلوقات تفكك بقايا الكائنات وتعيد العناصر للبيئة',['منتجات ضوئية','مستهلكات أولية فقط','عوامل غير حية'],'الفطريات وبعض البكتيريا محللات مهمة لدورة المواد.'),
        ('البيئة','السعة التحملية','أكبر عدد من الأفراد يمكن للبيئة دعمه على المدى الطويل',['معدل ولادة ثابت','عدد المفترسات فقط','عدد الأنواع في المجتمع'],'تحدد الموارد والمنافسة السعة التحملية.'),
        ('البيئة','التعاقب البيئي','تغير تدريجي في تركيب المجتمع الحيوي عبر الزمن',['انقراض جميع الأنواع فورًا','انتقال الطاقة بين المستويات','زيادة عدد الكروموسومات'],'قد يكون التعاقب أوليًا بلا تربة أو ثانويًا مع بقاء التربة.'),
        ('البيئة','التنوع الحيوي','تنوع الجينات والأنواع والأنظمة البيئية',['عدد أفراد نوع واحد فقط','كمية الماء في النظام','معدل التنفس الخلوي'],'ارتفاع التنوع الحيوي يعزز مرونة الأنظمة البيئية.'),
    ]


def add_bio_extra(bank: Bank,target:int):
    facts=bio_facts(); i=0
    attempts=0
    while bank.count('الأحياء وعلم البيئة')<target and attempts<20000:
        attempts+=1
        unit,term,desc,wrongs,exp=facts[i%len(facts)]
        variant=(i//len(facts))%4
        if variant==0:
            q=f'أي تركيب أو مفهوم يؤدي الوظيفة الآتية: {desc}؟'; c=term; ds=[f[1] for f in facts if f[0]==unit and f[1]!=term][:3]
        elif variant==1:
            q=f'أي مما يأتي يعد مثالًا أو وصفًا صحيحًا لـ {term}؟'; c=desc; ds=wrongs
        elif variant==2:
            q=f'طالب يراجع مفهوم {term}. أي عبارة ينبغي أن يختارها؟'; c=desc; ds=wrongs[::-1]
        else:
            q=f'ما العبارة التي تميز {term} عن المفاهيم القريبة منه؟'; c=desc; ds=wrongs
        bank.add(subject='الأحياء وعلم البيئة',unit=unit,skill=term,question=q,correct=c,distractors=ds,explanation=exp,difficulty='سهل' if variant in (0,1) else 'متوسط')
        i+=1


def add_bio_images(bank: Bank,target:int):
    i=0
    attempts=0
    while bank.count('الأحياء وعلم البيئة')<target and attempts<20000:
        attempts+=1
        kind=i%4
        if kind==0:
            body='<ellipse class="fill2" cx="320" cy="180" rx="200" ry="120"/><circle class="fill" cx="320" cy="180" r="55"/><circle cx="235" cy="130" r="20" fill="#1a86b8"/><circle cx="410" cy="220" r="22" fill="#4bbb9e"/><text class="label" x="312" y="188">1</text>'
            image=write_svg(f'bio_cell_{i:03d}.svg',body)
            bank.add(subject='الأحياء وعلم البيئة',unit='الخلية',skill='النواة',question='أي تركيب يمثله الرقم 1 ويحتوي معظم المادة الوراثية للخلية حقيقية النواة؟',correct='النواة',distractors=['الغشاء البلازمي','الريبوسوم','السيتوبلازم'],explanation='النواة هي العضية المحاطة بغشاء التي تحتوي معظم DNA في الخلية حقيقية النواة.',difficulty='سهل',image=image,image_alt='رسم مبسط لخلية حقيقية النواة تظهر فيها النواة')
        elif kind==1:
            body='<rect class="fill2" x="80" y="80" width="480" height="200" rx="24"/><circle cx="150" cy="180" r="26" fill="#1a86b8"/><circle cx="250" cy="180" r="26" fill="#1a86b8"/><circle cx="390" cy="180" r="26" fill="#4bbb9e"/><circle cx="500" cy="180" r="26" fill="#4bbb9e"/><path class="line" d="M190 180 L210 180"/><path class="line" d="M290 180 L350 180"/><path class="line" d="M430 180 L460 180"/><path class="line" d="M285 180 L355 180"/><path d="M355 180 L335 168 L335 192 Z" fill="#153653"/>'
            image=write_svg(f'bio_diffusion_{i:03d}.svg',body)
            bank.add(subject='الأحياء وعلم البيئة',unit='الخلية',skill='الانتشار',question='أي عملية يمثلها انتقال الجزيئات في الشكل دون استهلاك مباشر للطاقة؟',correct='الانتشار',distractors=['النقل النشط','البلعمة','الإخراج الخلوي'],explanation='الحركة من تركيز مرتفع إلى منخفض دون ATP تمثل الانتشار.',difficulty='سهل',image=image,image_alt='جزيئات تنتقل من منطقة عالية التركيز إلى منخفضة التركيز')
        elif kind==2:
            body='<circle class="fill" cx="120" cy="180" r="42"/><circle class="fill2" cx="270" cy="180" r="42"/><circle class="fill" cx="430" cy="180" r="42"/><path class="line" d="M165 180 L220 180"/><path class="line" d="M315 180 L380 180"/><text class="small" x="110" y="188">P</text><text class="small" x="260" y="188">R</text><text class="small" x="420" y="188">F</text>'
            image=write_svg(f'bio_food_chain_{i:03d}.svg',body)
            bank.add(subject='الأحياء وعلم البيئة',unit='البيئة',skill='السلسلة الغذائية',question='في السلسلة الغذائية الموضحة: P نبات، وR أرنب، وF ثعلب. ما دور R؟',correct='مستهلك أولي',distractors=['منتج','محلل','مستهلك ثانوي'],explanation='الأرنب يتغذى مباشرة على المنتج (النبات)، لذلك يعد مستهلكًا أوليًا.',difficulty='سهل',image=image,image_alt='سلسلة غذائية نبات ثم أرنب ثم ثعلب')
        else:
            body='<path class="line" d="M100 280 C160 260 190 180 250 170 C320 160 350 90 430 85 C500 80 520 125 550 120"/><line class="guide" x1="90" y1="280" x2="550" y2="280"/><text class="small" x="520" y="320">t</text><text class="small" x="35" y="70">N</text><line class="soft" x1="80" y1="110" x2="560" y2="110"/><text class="tiny" x="525" y="100">K</text>'
            image=write_svg(f'bio_population_{i:03d}.svg',body)
            bank.add(subject='الأحياء وعلم البيئة',unit='البيئة',skill='نمو الجماعة',question='ماذا يمثل الخط الأفقي في الرسم البياني لنمو الجماعة؟',correct='السعة التحملية للبيئة',distractors=['معدل الطفرات','عدد الأنواع في المجتمع','معدل البناء الضوئي'],explanation='الخط الأفقي يمثل الحد الذي تستطيع موارد البيئة دعمه بصورة مستقرة، وهو السعة التحملية.',difficulty='متوسط',image=image,image_alt='منحنى نمو جماعة يقترب من خط أفقي يمثل السعة التحملية')
        i+=1


def main():
    existing=json.loads(QUESTIONS_PATH.read_text(encoding='utf-8'))
    bank=Bank(existing)

    # 1) Conceptual core mapped from the four uploaded books.
    add_fact_variants(bank,'فيزياء',physics_facts(),72)
    add_physics_numeric(bank,270)
    add_physics_images(bank,300)

    add_fact_variants(bank,'كيمياء',chemistry_facts(),72)
    add_chem_numeric(bank,265)
    add_chem_images(bank,300)

    add_fact_variants(bank,'رياضيات',math_facts(),50)
    add_math_numeric(bank,260)
    add_math_images(bank,300)

    add_fact_variants(bank,'الأحياء وعلم البيئة',bio_facts(),100)
    add_bio_extra(bank,260)
    add_bio_images(bank,300)

    # Remove four legacy disguised duplicate distractors from the earlier Qudrat bank.
    legacy_replacements = {
        260011: '7/24', 260012: '19/30', 260015: '23/24', 260016: '8/15',
    }
    for q in bank.questions:
        pid = q.get('public_id')
        if pid in legacy_replacements:
            q['choices'] = [legacy_replacements[pid] if str(x).endswith('(1)') else x for x in q.get('choices', [])]

    # Public IDs continue after Qudrat 263000.
    for idx,q in enumerate(bank.questions, start=1):
        q['public_id']=260000+idx
        q['created_year']=2026

    QUESTIONS_PATH.write_text(json.dumps(bank.questions,ensure_ascii=False,indent=2),encoding='utf-8')
    report={
        'total_questions':len(bank.questions),
        'qudrat_questions':sum(1 for q in bank.questions if q.get('exam')!='تحصيلي'),
        'tahsili_questions':sum(1 for q in bank.questions if q.get('exam')=='تحصيلي'),
        'by_subject':dict(Counter(q.get('subject') for q in bank.questions if q.get('exam')=='تحصيلي')),
        'image_questions':sum(1 for q in bank.questions if q.get('exam')=='تحصيلي' and q.get('image')),
        'public_id_first_tahsili':min(q['public_id'] for q in bank.questions if q.get('exam')=='تحصيلي'),
        'public_id_last':max(q['public_id'] for q in bank.questions),
        'explanation_modes':dict(Counter(q.get('explanation_mode') for q in bank.questions if q.get('exam')=='تحصيلي')),
    }
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
