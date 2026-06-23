"""Validate Sprint 72 exact summary links and explanation policy."""
from __future__ import annotations
import ast, json, sqlite3, subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app.py'; JS=ROOT/'src/ui/sprint72_exact_links_explanations.js'; CSS=ROOT/'src/ui/sprint72_exact_links_explanations.css'; API=ROOT/'src/api/server.py'
Q=ROOT/'data/questions.json'; S=ROOT/'data/smart_summaries.json'; DB=ROOT/'data/suhail_learning.db'; RUNTIME=ROOT/'docs/reports/SPRINT_72_RUNTIME_QA.json'
source=APP.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8'); css=CSS.read_text(encoding='utf-8'); api=API.read_text(encoding='utf-8')
questions=json.loads(Q.read_text(encoding='utf-8')); summaries=json.loads(S.read_text(encoding='utf-8')); runtime=json.loads(RUNTIME.read_text(encoding='utf-8')) if RUNTIME.exists() else {}
blocks={str(b.get('id')):(s,b) for s in summaries for b in s.get('knowledge_blocks',[])}; sids={str(s.get('summary_id') or s.get('id')) for s in summaries}
node=subprocess.run(['node','--check',str(JS)],capture_output=True,text=True)
try: ast.parse(source); pyok=True
except SyntaxError: pyok=False
modes=Counter((str(q.get('difficulty')),str(q.get('explanation_mode'))) for q in questions)
physics=[q for q in questions if q.get('subject')=='فيزياء']; nonphysics=[q for q in questions if q.get('subject')!='فيزياء']
valid_links=[q for q in physics if str(q.get('summary_id')) in sids and str(q.get('summary_block_id')) in blocks and blocks[str(q.get('summary_block_id'))][0].get('summary_id')==q.get('summary_id')]
exact_title=[q for q in physics if q.get('summary_block_title') and q.get('skill') and (q.get('summary_block_title')==q.get('skill') or q.get('summary_link_score',0)>=40)]
with sqlite3.connect(DB) as con: db_count=con.execute('select count(*) from questions').fetchone()[0]
checks={
 'python_syntax':pyok,'javascript_syntax':node.returncode==0,'sprint72_assets_injected':'sprint72_exact_links_explanations.css' in source and 'sprint72_exact_links_explanations.js' in source,
 'loaded_after_sprint71':source.find('Sprint 72 owns exact')>source.find('Sprint 71 is the final'),
 'api_release_72':'RELEASE = "72.0.0"' in api,'question_total':len(questions),'summary_total':len(summaries),'db_question_total':db_count,
 'easy_none':modes.get(('سهل','none'),0),'medium_brief':modes.get(('متوسط','brief'),0),'hard_full':modes.get(('صعب','full'),0),
 'easy_visible_explanations':sum(bool(str(q.get('explain') or '').strip()) for q in questions if q.get('difficulty')=='سهل'),
 'medium_hard_missing':sum(not bool(str((q.get('explanation') or {}).get('summary') or '').strip()) for q in questions if q.get('difficulty') in ('متوسط','صعب')),
 'physics_links_valid':len(valid_links),'physics_links_exact_or_high_score':len(exact_title),'nonphysics_guessed_links':sum(bool(q.get('summary_id') or q.get('summary_block_id')) for q in nonphysics),
 'related_filter_exact':'ref.unit === currentSummaryUnit;' in source and '|| ref.unit' not in source[source.find('function renderRelatedQuestionsPage'):source.find('function openSummariesHome')],
 'exact_modal':'s72LinkModal' in js and 'openFull(q)' in js,'exact_focus':'s72-summary-focus' in js and 's72-linked-lesson' in css,
 'result_link':'s72-result-link' in js and 'decorateResults' in js,'explicit_only':'if(!q||!q.summary_id||!q.summary_block_id)return null' in js,
 'explanation_policy_v3':sum(q.get('explanation_policy')=='difficulty_based_pedagogical_v3' for q in questions),
 'medium_hard_min_length':min([len(str(q.get('explain') or '').strip()) for q in questions if q.get('difficulty') in ('متوسط','صعب')] or [0]),
 'result_render_idempotent':'card.dataset.s72Result===signature' in js and 'card.dataset.s72Result=signature' in js,
 'runtime_interaction_qa':runtime.get('passed') is True and runtime.get('errors')==[],
}
checks['passed']=all(v for k,v in checks.items() if isinstance(v,bool)) and checks['question_total']==5400 and checks['summary_total']==72 and checks['db_question_total']==5400 and checks['easy_none']==1968 and checks['medium_brief']==3137 and checks['hard_full']==295 and checks['easy_visible_explanations']==0 and checks['medium_hard_missing']==0 and checks['physics_links_valid']==600 and checks['physics_links_exact_or_high_score']==600 and checks['nonphysics_guessed_links']==0 and checks['explanation_policy_v3']==5400 and checks['medium_hard_min_length']>=30
out=ROOT/'docs/reports/SPRINT_72_CHECKS.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2));raise SystemExit(0 if checks['passed'] else 1)
