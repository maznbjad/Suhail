from __future__ import annotations
import json, re, sqlite3, subprocess, sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
qs=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
checks={}
checks['total_3000']=len(qs)==3000
checks['quant_1500']=sum(q.get('exam')=='قدرات كمي' for q in qs)==1500
checks['verbal_1500']=sum(q.get('exam')=='قدرات لفظي' for q in qs)==1500
pub=[q.get('public_id') for q in qs]
checks['public_ids_contiguous']=pub==list(range(260001,263001))
checks['unique_internal_ids']=len({q.get('id') for q in qs})==len(qs)
checks['unified_bank_only']=all(q.get('bank')=='قدرات موحد' and 'test_format' not in q and 'delivery_mode' not in q for q in qs)
checks['api_has_no_format_filter']='test_format' not in (ROOT/'src/api/server.py').read_text(encoding='utf-8') and 'delivery_mode' not in (ROOT/'src/api/server.py').read_text(encoding='utf-8')
checks['answers_match']=all(len(q.get('choices',[]))==4 and len(set(q['choices']))==4 and q['choices'][int(q['correct'])]==q.get('answer') for q in qs)
checks['explanation_modes_valid']=all(q.get('explanation_mode') in {'none','brief','full'} for q in qs)
checks['easy_without_long_explanation']=sum(q.get('explanation_mode')=='none' for q in qs)>=500
checks['close_choice_is_selective']=0 < sum(bool(q.get('explanation',{}).get('similar_choices')) for q in qs) < 300
q154=next(q for q in qs if q.get('public_id')==260154)
checks['question_260154_fixed']=q154.get('question')=='ما مساحة المستطيل الموضح في الشكل؟' and q154.get('image','').endswith('rectangle_3.svg')
image_q=[q for q in qs if q.get('image')]
checks['image_count']=len(image_q)>=80
checks['no_literal_figure_numbers']=all(not re.search(r'(?:المستطيل|الشكل المركب|الشكل) رقم\s*\d+',q.get('question','')) for q in image_q)
checks['all_images_exist']=all((ROOT/q['image']).exists() for q in image_q)
transparent=True
for q in image_q:
    p=ROOT/q['image']
    try:
        ET.parse(p)
        txt=p.read_text(encoding='utf-8')
        if re.search(r'<rect\s+width="100%"\s+height="100%"[^>]*fill=',txt):
            transparent=False
    except Exception:
        transparent=False
checks['svg_valid_and_no_full_background']=transparent
with sqlite3.connect(ROOT/'data/suhail_learning.db') as conn:
    db_count=conn.execute('select count(*) from questions').fetchone()[0]
checks['sqlite_3000']=db_count==3000
try:
    subprocess.run([sys.executable,'-m','py_compile',str(ROOT/'app.py'),str(ROOT/'scripts/generate_complete_qudrat_bank.py')],check=True,capture_output=True)
    checks['python_syntax']=True
except Exception:
    checks['python_syntax']=False
try:
    subprocess.run(['node','--check',str(ROOT/'src/ui/sprint62_question_standard.js')],check=True,capture_output=True)
    checks['javascript_syntax']=True
except Exception:
    checks['javascript_syntax']=False
checks['passed']=all(checks.values())
out=ROOT/'docs/reports/SPRINT_65_CHECKS.json'
out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
raise SystemExit(0 if checks['passed'] else 1)
