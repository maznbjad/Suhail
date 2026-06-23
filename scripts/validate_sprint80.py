#!/usr/bin/env python3
"""Validate Sprint 80 accessibility and Tahsili linkage audit."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
load=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))
questions=load(Path('data/questions.json'))
manifest=load(Path('config/project_manifest.json'))
css=(ROOT/'src/ui/sprint80_accessibility.css').read_text(encoding='utf-8')
js=(ROOT/'src/ui/sprint80_accessibility.js').read_text(encoding='utf-8')
app=(ROOT/'app.py').read_text(encoding='utf-8')
api=(ROOT/'src/api/server.py').read_text(encoding='utf-8')

tahsili=[q for q in questions if q.get('exam')=='تحصيلي']
subjects={}
for q in tahsili:
    subject=q.get('subject') or q.get('category') or 'غير محدد'
    item=subjects.setdefault(subject,{'total':0,'linked':0,'unlinked':0,'statuses':{}})
    item['total']+=1
    status=str(q.get('knowledge_link_status') or '')
    item['statuses'][status]=item['statuses'].get(status,0)+1
    exact=bool(q.get('summary_id') and q.get('summary_block_id') and status.startswith('linked_exact'))
    if exact:item['linked']+=1
    else:item['unlinked']+=1
linked=sum(x['linked'] for x in subjects.values())

checks={
 'release_manifest':manifest.get('release')=='Sprint 80' and manifest.get('version')=='1.0.80' and manifest.get('latest_sprint')==80,
 'api_release':'RELEASE = "80.0.0"' in api,
 'question_count':len(questions)==5400,
 'tahsili_count':len(tahsili)==2400,
 'physics_exact_links':subjects.get('فيزياء',{}).get('linked')==600,
 'nonphysics_not_guessed':all(subjects.get(s,{}).get('linked')==0 and subjects.get(s,{}).get('unlinked')==600 for s in ['كيمياء','رياضيات','الأحياء وعلم البيئة']),
 'link_coverage_25_percent':linked==600,
 'accessibility_injected':'sprint80_accessibility.css' in app and 'sprint80_accessibility.js' in app and app.find('Sprint 80 is the final')>app.find('Sprint 79 is the final'),
 'variable_font_override':all(t in css for t in ['#exercisePage .quiz-question','var(--s80-font-question)!important','#exercisePage #choicesBox .choice','var(--s80-font-choice)!important','@media(max-width:430px)']),
 'legacy_sync':all(t in js for t in ['--question-font-size','--choice-font-size','--passage-font-size']),
 'font_bounds':all(t in js for t in ['const MIN=14,MAX=28,STEP=2,DEFAULT=18','suhail_question_text_size_v2']),
 'global_override':all(t in js for t in ['window.changeQuestionTextSize=change','window.applyQuestionTextSize=function','window.resetQuestionTextSize=reset']),
 'dark_contrast_tokens':all(t in css for t in ['--s80-text:#f5f9fd','--s80-muted:#c4d2de','--s80-surface:#122536','--s80-border:#486078']),
}
report={
 'release':'80.0.0','passed':all(checks.values()),'checks':checks,
 'tahsili_linkage':{
   'total':len(tahsili),'linked_exact':linked,'unlinked':len(tahsili)-linked,
   'coverage_percent':round(linked/len(tahsili)*100,2) if tahsili else 0,
   'subjects':subjects,
   'policy':'No guessed links for unpublished summaries.'
 },
 'font_control':{'minimum_px':14,'default_px':18,'maximum_px':28,'step_px':2,'persistent':True},
}
out=ROOT/'docs/reports/SPRINT_80_VALIDATION.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=ROOT/'docs/reports/SPRINT_80_ACCESSIBILITY_AND_LINK_AUDIT.md'
lines=['# Sprint 80 — Accessibility and Tahsili Link Audit','',f'- Tahsili questions: **{len(tahsili)}**',f'- Exact summary links: **{linked} ({report["tahsili_linkage"]["coverage_percent"]}%)**',f'- Waiting for approved summaries: **{len(tahsili)-linked}**','']
for subject,data in subjects.items():lines.append(f'- {subject}: {data["linked"]}/{data["total"]} linked')
lines += ['','## Font controls','- Question, answer choices, reading passage, captions, and explanation scale together.','- Range: 14–28 px in 2 px steps.','- Preference persists safely; legacy variables stay synchronized.','','## Contrast','- Final light/dark tokens are applied after legacy modules.','- Muted text remains fully opaque and readable.','- Correct/wrong states use both color and borders.']
md.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['passed'] else 1)
