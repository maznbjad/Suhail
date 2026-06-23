#!/usr/bin/env python3
"""Validate the final Sprint 79 physics mastery release."""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
load=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))
summaries=load(Path('data/smart_summaries.json'))
questions=load(Path('data/questions.json'))
manifest=load(Path('config/project_manifest.json'))
template=load(Path('data/content/physics_lesson_template_v2.json'))
app=(ROOT/'app.py').read_text(encoding='utf-8')
ui=(ROOT/'src/ui/sprint79_physics_mastery.js').read_text(encoding='utf-8')
css=(ROOT/'src/ui/sprint79_physics_mastery.css').read_text(encoding='utf-8')
api=(ROOT/'src/api/server.py').read_text(encoding='utf-8')
required=template['required_sections']
checks={}
checks['release_manifest']=manifest.get('release')=='Sprint 79' and manifest.get('version')=='1.0.79' and manifest.get('latest_sprint')==79
checks['api_release']='RELEASE = "79.0.0"' in api
checks['summary_count']=len(summaries)==72
checks['question_count']=len(questions)==5400
physics=[q for q in questions if q.get('subject')=='فيزياء']
checks['physics_question_count']=len(physics)==600
checks['template_every_lesson']=all(isinstance(s.get('learning_path_v2'),dict) and all(k in s['learning_path_v2'] for k in required) for s in summaries)
checks['minimum_content']=all(
 len(s['learning_path_v2']['prerequisites'])>=2 and len(s['learning_path_v2']['definitions'])>=3 and
 len(s['learning_path_v2']['formula_cards'])>=1 and len(s['learning_path_v2']['worked_examples'])>=3 and
 len(s['learning_path_v2']['dont_confuse'])>=2 and len(s['learning_path_v2']['exam_patterns'])>=4 and
 len(s['learning_path_v2']['practice_questions'])==5
 for s in summaries)
checks['mastery_policy']=all(s['learning_path_v2']['mastery'].get('minimum_score_percent')==80 and s['learning_path_v2']['mastery'].get('required_correct')==4 for s in summaries)
checks['unique_summary_ids']=len({s['summary_id'] for s in summaries})==72
all_blocks=[(s['summary_id'],b) for s in summaries for b in s.get('knowledge_blocks',[])]
checks['unique_block_ids']=len({b['id'] for _,b in all_blocks})==len(all_blocks)
summary_map={s['summary_id']:s for s in summaries};block_map={b['id']:(sid,b) for sid,b in all_blocks}
invalid=[]
for q in physics:
 sid,bid=q.get('summary_id'),q.get('summary_block_id')
 if not sid or not bid or sid not in summary_map or bid not in block_map or block_map[bid][0]!=sid: invalid.append(q.get('id'))
checks['all_physics_exact_links_valid']=not invalid
checks['linked_lesson_policy']=len({q.get('summary_id') for q in physics})==22 and sum(1 for s in summaries if s.get('linked_question_count',0)==0)==50
checks['practice_answers']=all(all(0<=q['correct_index']<len(q['options']) and q.get('explanation','').strip() for q in s['practice_questions']) for s in summaries)
checks['practice_unique_per_lesson']=all(len({q['question'].strip() for q in s['practice_questions']})==5 for s in summaries)
checks['difficulty_ladder']=all(s['practice_questions'][-1].get('difficulty')=='صعب' for s in summaries)
checks['ui_injected']='sprint79_physics_mastery.css' in app and 'sprint79_physics_mastery.js' in app and app.find('Sprint 79 is the final')>app.find('Sprint 72 owns exact')
checks['deep_link_override']='window.s79OpenReference' in ui and 'window.s71OpenUnit=function' in ui
checks['ui_sections']=all(token in ui for token in ['قبل أن تبدأ','الفكرة من الصفر','القوانين بمعناها','أمثلة محلولة متدرجة','اختبر فهمك — 5 أسئلة','خلاصة الدرس'])
checks['dark_mode']='[data-theme="dark"]' in css and '--s70-text:#f4f7fc' in css
checks['no_mutation_observer_in_s79']='MutationObserver' not in ui
# Guard against the known sibling-lesson routing regressions found during QA.
def titles(unit,title):
 s=next(x for x in summaries if x['unit']==unit and x['title']==title)
 return ' | '.join(f['title']+' '+f['formula'] for f in s['formula_cards'])
checks['projectile_routing']='السرعة العمودية النهائية' in titles('الحركة في بعدين','حركة المقذوف') and 'السرعة العمودية النهائية' not in titles('الحركة في بعدين','السرعة المتجهة النسبية')
checks['wave_routing']='التداخل الهدّام' in titles('الاهتزازات والموجات','سلوك الموجات') and 'التداخل الهدّام' not in titles('الاهتزازات والموجات','الحركة الدورية')
checks['nuclear_routing']='ألفا' in titles('الفيزياء النووية','الاضمحلال النووي والتفاعلات النووية') and 'ألفا' not in titles('الفيزياء النووية','النواة')
# DB is optional during source validation but, when present, must match the JSON bank.
db=ROOT/'data/suhail_learning.db'
if db.exists():
 with sqlite3.connect(db) as c:
  checks['db_question_count']=c.execute('select count(*) from questions').fetchone()[0]==5400
else: checks['db_question_count']=False
report={
 'release':'79.0.0','checks':checks,'passed':all(checks.values()),
 'metrics':{
  'summaries':len(summaries),'questions':len(questions),'physics_questions':len(physics),
  'knowledge_blocks':len(all_blocks),'internal_mastery_questions':sum(len(s['practice_questions']) for s in summaries),
  'exact_external_links':len(physics),'lessons_with_external_links':22,'lessons_without_guessed_links':50,
 },
 'invalid_physics_links':invalid[:20],
 'editorial_status':'قالب ومحتوى داخلي مكتملان آليًا؛ يوصى بمراجعة بشرية تخصصية قبل النشر العام النهائي.'
}
out=ROOT/'docs/reports/SPRINT_79_VALIDATION.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['passed'] else 1)
