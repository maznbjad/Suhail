#!/usr/bin/env python3
from pathlib import Path
import json, sqlite3, re, subprocess, sys
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
q=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
checks={}
checks['total_questions']=len(q)==5400
checks['qudrat_3000']=sum(x.get('exam')!='تحصيلي' for x in q)==3000
checks['tahsili_2400']=sum(x.get('exam')=='تحصيلي' for x in q)==2400
expected={'فيزياء':600,'كيمياء':600,'رياضيات':600,'الأحياء وعلم البيئة':600}
actual={s:sum(x.get('exam')=='تحصيلي' and x.get('subject')==s for x in q) for s in expected}
checks['subject_distribution']=actual==expected
ids=[x.get('id') for x in q]; pids=[x.get('public_id') for x in q]
checks['unique_internal_ids']=len(ids)==len(set(ids))==len(q)
checks['public_ids_contiguous']=pids==list(range(260001,260001+len(q)))
checks['choices_and_answers']=all(len(x.get('choices',[]))==4 and len(set(map(str,x.get('choices',[]))))==4 and 0<=int(x.get('correct',-1))<4 and str(x.get('answer'))==str(x['choices'][int(x['correct'])]) for x in q)
checks['explanation_schema']=all(isinstance(x.get('explanation'),dict) and 'summary' in x['explanation'] and x.get('explanation_mode') in {'none','brief','full'} for x in q)
imgs=[x.get('image') for x in q if x.get('image')]
checks['all_images_exist']=all((ROOT/i).exists() for i in imgs)
svg_ok=True
for i in imgs:
    if str(i).lower().endswith('.svg'):
        try: ET.parse(ROOT/i)
        except Exception: svg_ok=False; break
checks['svg_valid']=svg_ok
inv=json.loads((ROOT/'data/source_inventory/tahsili_inventory_report.json').read_text(encoding='utf-8'))
checks['inventory_raw_8802']=inv.get('raw_candidates')==8802
checks['inventory_unique_7116']=inv.get('unique_exact_contexts')==7116
with sqlite3.connect(ROOT/'data/suhail_learning.db') as c:
    tables={x[0] for x in c.execute("select name from sqlite_master where type='table'")}
    count=None
    for t in ('questions','question_bank'):
        if t in tables:
            count=c.execute(f'select count(*) from {t}').fetchone()[0];break
checks['sqlite_5400']=count==5400
js=(ROOT/'src/ui/sprint68_feedback_control.js').read_text(encoding='utf-8')
checks['toggle_default_off']='window.SUHAIL_SHOW_RESULT=v' in js and "localStorage.getItem(KEY)==='1'" in js
checks['label_free_feedback']='الإجابة الصحيحة' not in js and 'التوضيح' not in js
checks['s68_injected']='sprint68_feedback_control.js' in (ROOT/'app.py').read_text(encoding='utf-8')
report={'ok':all(checks.values()),'checks':checks,'counts':{'total':len(q),'qudrat':3000,'tahsili':2400,'by_subject':actual,'image_questions':len(imgs),'inventory_raw':inv.get('raw_candidates'),'inventory_unique':inv.get('unique_exact_contexts'),'last_public_id':max(pids)},'notes':['Source inventory candidates are not automatically release eligible.','Student-facing questions are rewritten and independently solved.']}
out=ROOT/'docs/reports/SPRINT_68_CHECKS.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['ok'] else 1)
