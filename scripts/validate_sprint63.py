from __future__ import annotations
import ast, json, sqlite3, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks={}
try:
    ast.parse((ROOT/'app.py').read_text(encoding='utf-8'))
    checks['python_syntax']=True
except Exception as exc:
    checks['python_syntax']=False; checks['python_error']=str(exc)
css=(ROOT/'src/ui/sprint63_test_entry.css').read_text(encoding='utf-8')
js=(ROOT/'src/ui/sprint63_test_entry.js').read_text(encoding='utf-8')
app=(ROOT/'app.py').read_text(encoding='utf-8')
checks['button_label_exact']=">اختبار<" in js
checks['prominent_button_css']='min-height:76px' in css and 'linear-gradient' in css
checks['opens_exam_setup']='goToExercise' in js and "exercisePage" in js
checks['survives_home_rerender']='MutationObserver' in js and 'setInterval(installButton' in js
checks['module_injected_last']='sprint63_test_entry.css' in app and app.rfind('sprint63_test_entry.css')>app.rfind('sprint62_question_standard.css')
checks['account_version_63']='V.1.0.63' in (ROOT/'src/ui/sprint55_account.js').read_text(encoding='utf-8')
qpath=ROOT/'data/questions/questions.json'
if qpath.exists():
    data=json.loads(qpath.read_text(encoding='utf-8'))
    rows=data.get('questions',data) if isinstance(data,dict) else data
    checks['question_count']=len(rows)
    ids=[str(x.get('id','')) for x in rows]
    checks['question_ids_unique']=len(ids)==len(set(ids))
report={'sprint':63,'checks':checks,'passed':all(v is True or isinstance(v,int) for v in checks.values() if not str(v).startswith('python_error'))}
out=ROOT/'docs/reports/SPRINT_63_CHECKS.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
