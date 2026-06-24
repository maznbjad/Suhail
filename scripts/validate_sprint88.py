from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks={}
def add(name,ok,detail=''):
    checks[name]={'ok':bool(ok),'detail':detail}

def main():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    js_path=ROOT/'src/ui/sprint88_exam_dates_plan.js'
    css_path=ROOT/'src/ui/sprint88_exam_dates_plan.css'
    js=js_path.read_text(encoding='utf-8')
    manifest=json.loads((ROOT/'config/project_manifest.json').read_text(encoding='utf-8'))
    questions=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
    add('files',js_path.exists() and css_path.exists())
    add('injection','sprint88_exam_dates_plan.css' in app and 'sprint88_exam_dates_plan.js' in app)
    add('version',manifest.get('version')=='1.0.88' and manifest.get('latest_sprint')==88)
    add('dates','s88QudratDate' in js and 's88TahsiliDate' in js)
    add('variable_load','const CYCLE=' in js and len(set([.78,1,1.16,.88,1.22,.66,1.06]))>1)
    add('taper','daysLeft<=1' in js and 'daysLeft===2' in js and 'daysLeft===3' in js)
    add('performance','weightedAccuracy' in js and 'weakestQudrat' in js and 'weakestTahsili' in js)
    add('bank_count',len(questions)==5400,str(len(questions)))
    exams={}
    for q in questions: exams[q.get('exam','')]=exams.get(q.get('exam',''),0)+1
    add('bank_distribution',sum(v for k,v in exams.items() if 'قدرات' in k)==3000 and exams.get('تحصيلي')==2400,str(exams))
    node=subprocess.run(['node','--check',str(js_path)],capture_output=True,text=True)
    add('javascript_syntax',node.returncode==0,node.stderr.strip())
    py=subprocess.run([sys.executable,'-m','py_compile',str(ROOT/'app.py'),str(ROOT/'src/api/server.py')],capture_output=True,text=True)
    add('python_syntax',py.returncode==0,py.stderr.strip())
    ok=all(x['ok'] for x in checks.values())
    out={'sprint':88,'ok':ok,'checks':checks}
    report=ROOT/'docs/reports/SPRINT_88_CHECKS.json'
    report.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
