#!/usr/bin/env python3
from __future__ import annotations
import json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
qs=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
errors=[]
ids=set(); pids=set(); normalized=set(); image_count=0
subjects=Counter(); modes=Counter()
for i,q in enumerate(qs):
    qid=q.get('id'); pid=q.get('public_id')
    if not qid or qid in ids: errors.append(f'duplicate/missing id at {i}: {qid}')
    ids.add(qid)
    if not isinstance(pid,int) or pid in pids: errors.append(f'duplicate/missing public_id: {pid}')
    pids.add(pid)
    text=re.sub(r'\s+',' ',str(q.get('question','')).strip())
    key=(text+'|'+str(q.get('image',''))+'|'+str(q.get('passage',''))).lower()
    if not text: errors.append(f'empty question {qid}')
    if key in normalized: errors.append(f'duplicate question text {qid}')
    normalized.add(key)
    choices=q.get('choices') or []
    if len(choices)!=4 or len(set(map(str,choices)))!=4: errors.append(f'bad choices {qid}: {choices}')
    c=q.get('correct')
    if not isinstance(c,int) or not 0<=c<4: errors.append(f'bad correct index {qid}: {c}')
    elif str(choices[c])!=str(q.get('answer')): errors.append(f'answer mismatch {qid}')
    if any(re.search(r'\(\d+\)$',str(x)) for x in choices): errors.append(f'disguised duplicate {qid}')
    if q.get('exam')=='تحصيلي':
        subject=q.get('subject'); subjects[subject]+=1; modes[q.get('explanation_mode')]+=1
        if subject not in {'فيزياء','كيمياء','رياضيات','الأحياء وعلم البيئة'}: errors.append(f'bad subject {qid}: {subject}')
        if not isinstance(q.get('explanation'),dict): errors.append(f'missing explanation dict {qid}')
        if not str(q.get('explain','')).strip(): errors.append(f'missing explanation text {qid}')
        if pid<263001: errors.append(f'bad tahsili public id {qid}: {pid}')
    image=q.get('image')
    if image:
        image_count+=1
        path=ROOT/image
        if not path.exists(): errors.append(f'missing image {qid}: {image}')
        elif path.suffix.lower()=='.svg':
            try: ET.parse(path)
            except Exception as exc: errors.append(f'bad svg {qid}: {exc}')
        if not q.get('image_alt'): errors.append(f'missing image alt {qid}')

if len(qs)!=4200: errors.append(f'count {len(qs)} != 4200')
if sorted(pids)!=list(range(260001,264201)): errors.append('public ids are not continuous 260001..264200')
expected={'فيزياء':300,'كيمياء':300,'رياضيات':300,'الأحياء وعلم البيئة':300}
if dict(subjects)!=expected: errors.append(f'subject counts {dict(subjects)}')

with sqlite3.connect(ROOT/'data/suhail_learning.db') as con:
    db_count=con.execute('select count(*) from questions').fetchone()[0]
if db_count!=len(qs): errors.append(f'sqlite mismatch {db_count}!={len(qs)}')

result={'ok':not errors,'question_count':len(qs),'subjects':dict(subjects),'image_questions_total':image_count,'tahsili_explanation_modes':dict(modes),'errors':errors[:100]}
out=ROOT/'docs/reports/SPRINT_67_CHECKS.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
if errors: sys.exit(1)
