"""Validate Sprint 60 summary content safety and dark-mode contrast."""
from __future__ import annotations
import ast, json, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app.py'
JS=ROOT/'src/ui/sprint59_summaries_navigation.js'
CSS=ROOT/'src/ui/sprint60_summary_cleanup.css'
SMART=ROOT/'data/smart_summaries.json'
source=APP.read_text(encoding='utf-8')
tree=ast.parse(source)
assign={}
for node in tree.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in {'fallback_summaries_data','qiyas_summaries_seed'}:
                assign[target.id]=ast.literal_eval(node.value)
smart=json.loads(SMART.read_text(encoding='utf-8'))
counts=Counter((str(x.get('track') or x.get('exam') or ''),str(x.get('subject') or '')) for x in smart)
js=JS.read_text(encoding='utf-8')
css=CSS.read_text(encoding='utf-8')
checks={
    'python_syntax':True,
    'javascript_syntax':subprocess.run(['node','--check',str(JS)],capture_output=True,text=True).returncode==0,
    'generated_fallback_summaries_removed':assign.get('fallback_summaries_data')==[],
    'generated_qudrat_summaries_removed':assign.get('qiyas_summaries_seed')==[],
    'published_summary_count':len(smart),
    'published_summary_distribution':{f'{k[0]} / {k[1]}':v for k,v in counts.items()},
    'physics_only':len(smart)==72 and counts==Counter({('تحصيلي','فيزياء'):72}),
    'canonical_top_order':"exams:['تحصيلي','قدرات لفظي','قدرات كمي']" in js,
    'unpublished_sections_are_empty_states':"view:'empty'" in js and 'لا توجد ملخصات منشورة هنا حاليًا' in js,
    'physics_legacy_experience_preserved':'legacyOpenPhysics' in js and "subject==='فيزياء'" in js,
    'bottom_navigation_contract_preserved':'s59-exam-active' in js,
    'dark_text_high_contrast':'--s56-text:#f8fbff' in css and '--s56-muted:#d0dce7' in css,
    'dark_placeholders_readable':'#b8c8d6' in css,
    'catalog_visual_consistency':'.s59-catalog-grid' in css and '.s59-catalog-empty' in css,
    'sprint60_css_injected_after_sprint59':source.find('Sprint 60 is a content-safety')>source.find('Sprint 59 restores'),
}
checks['passed']=all(v is True for k,v in checks.items() if k not in {'published_summary_count','published_summary_distribution','passed'})
out=ROOT/'docs/reports/SPRINT_60_CHECKS.json'
out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
sys.exit(0 if checks['passed'] else 1)
