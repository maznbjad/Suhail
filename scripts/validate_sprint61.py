"""Validate Sprint 61 summaries visibility regression fix."""
from __future__ import annotations
import ast, hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app.py'
JS=ROOT/'src/ui/sprint59_summaries_navigation.js'
SMART=ROOT/'data/smart_summaries.json'
source=APP.read_text(encoding='utf-8')
js=JS.read_text(encoding='utf-8')
smart=json.loads(SMART.read_text(encoding='utf-8'))
physics=[x for x in smart if str(x.get('exam') or x.get('track') or 'تحصيلي').strip()=='تحصيلي' and str(x.get('subject') or '').strip()=='فيزياء']
checks={
  'python_syntax': True,
  'javascript_syntax': subprocess.run(['node','--check',str(JS)],capture_output=True,text=True).returncode==0,
  'physics_items_function_defined': 'function physicsItems()' in js,
  'physics_items_reads_smart_summaries': "typeof smartSummaries!=='undefined'" in js,
  'published_physics_count': len(physics),
  'physics_count_is_72': len(physics)==72,
  'gateway_shows_physics_availability': 'ملخص فيزياء' in js,
  'empty_sections_not_labeled_coming_soon': "'غير منشور'" in js,
  'fallback_no_longer_says_coming_soon': '<div class="soon-title">قريبًا</div>' not in source,
  'runtime_self_heal_for_gateway': "page?.id==='summariesPage'&&!state.richPhysics&&!page.querySelector('.s59-page')" in js,
  'no_new_nonphysics_summaries': len(smart)==72 and len(physics)==72,
}
checks['passed']=all(v is True for k,v in checks.items() if k not in {'published_physics_count','passed'}) and checks['published_physics_count']==72
out=ROOT/'docs/reports/SPRINT_61_CHECKS.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
sys.exit(0 if checks['passed'] else 1)
