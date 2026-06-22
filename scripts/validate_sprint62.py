#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
qs=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
checks={}; errors=[]; warnings=[]
def check(name,cond,detail=None):
    checks[name]={'passed':bool(cond),'detail':detail}
    if not cond: errors.append(name)
check('question_count_292',len(qs)==292,len(qs))
ids=[q.get('id') for q in qs]; pubs=[q.get('public_id') for q in qs]
check('unique_internal_ids',len(ids)==len(set(ids)) and all(ids),len(set(ids)))
check('public_ids_sequential',pubs==list(range(260001,260293)),[pubs[:3],pubs[-3:]])
check('public_ids_unique',len(pubs)==len(set(pubs)),len(set(pubs)))
check('unified_bank_no_format_fields',all('test_format' not in q and 'delivery_mode' not in q for q in qs),None)
check('all_have_explanation',all(str(q.get('explain','')).strip() for q in qs),sum(not str(q.get('explain','')).strip() for q in qs))
check('all_have_four_choices',all(isinstance(q.get('choices'),list) and len(q['choices'])==4 for q in qs),None)
check('answers_match',all(isinstance(q.get('correct'),int) and 0<=q['correct']<4 and str(q.get('answer'))==str(q['choices'][q['correct']]) for q in qs),None)
pilot=[q for q in qs if str(q.get('id','')).startswith('QDR-VIS-')]
check('pilot_image_questions_12',len(pilot)==12,len(pilot))
check('pilot_structured_explanations',all(isinstance(q.get('explanation'),dict) and q['explanation'].get('summary') and q.get('hint') for q in pilot),None)
check('pilot_close_choice_notes',all(isinstance(q.get('explanation',{}).get('similar_choices'),list) and len(q['explanation']['similar_choices'])>=1 for q in pilot),None)
images=[q for q in qs if q.get('image')]
missing=[]; broken=[]; backgrounds=[]
for q in images:
    p=ROOT/q['image']
    if not p.exists(): missing.append(q['image']); continue
    try: ET.parse(p)
    except Exception as e: broken.append(f"{q['image']}: {e}")
    txt=p.read_text(encoding='utf-8')
    if '<rect width="100%" height="100%"' in txt: backgrounds.append(q['image'])
check('image_count_33',len(images)==33,len(images))
check('all_images_exist',not missing,missing)
check('all_svgs_parse',not broken,broken)
check('full_canvas_backgrounds_removed',not backgrounds,backgrounds)
check('image_metadata_complete',all(q.get('image_alt') and q.get('image_zoom') is True and q.get('image_background')=='transparent' for q in images),None)
with sqlite3.connect(ROOT/'data/suhail_learning.db') as c:
    db_count=c.execute('select count(*) from questions').fetchone()[0]
check('sqlite_matches_json',db_count==len(qs),db_count)
app=(ROOT/'app.py').read_text(encoding='utf-8')
css=(ROOT/'src/ui/sprint62_question_standard.css').read_text(encoding='utf-8')
js=(ROOT/'src/ui/sprint62_question_standard.js').read_text(encoding='utf-8')
check('s62_module_injected','sprint62_question_standard.css' in app and 'sprint62_question_standard.js' in app,None)
check('public_id_ui','s62-public-id' in css and 'public_id' in js,None)
check('zoom_ui','s62-zoom' in css and 'openZoom' in js,None)
check('structured_explanation_ui','similar_choices' in js and 'تلميح سهيل' in js,None)
check('format_selector_removed','نمط اختبار القدرات' not in (ROOT/'src/ui/sprint58_question_bank.js').read_text(encoding='utf-8'),None)
commands=[
 [sys.executable,'-m','py_compile',str(ROOT/'app.py'),str(ROOT/'src/api/server.py')],
 ['node','--check',str(ROOT/'src/ui/sprint58_question_bank.js')],
 ['node','--check',str(ROOT/'src/ui/sprint62_question_standard.js')],
]
results=[]
for cmd in commands:
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    results.append({'cmd':cmd,'returncode':r.returncode,'stderr':r.stderr[-1000:]})
check('syntax_checks',all(r['returncode']==0 for r in results),results)
report={'release':'62.0.0','qa_passed':not errors,'errors':errors,'warnings':warnings,'checks':checks,'summary':{'questions':len(qs),'image_questions':len(images),'pilot_image_questions':len(pilot),'by_exam':dict(Counter(q.get('exam') for q in qs)),'next_public_id':260293}}
out=ROOT/'docs/reports/SPRINT_62_CHECKS.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if not errors else 1)
