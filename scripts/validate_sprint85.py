#!/usr/bin/env python3
from pathlib import Path
import json, py_compile, subprocess
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'config/project_manifest.json').read_text(encoding='utf-8'))
app=(root/'app.py').read_text(encoding='utf-8')
css=(root/'src/ui/sprint85_account_completion.css').read_text(encoding='utf-8')
js=(root/'src/ui/sprint85_account_completion.js').read_text(encoding='utf-8')
api=(root/'src/api/server.py').read_text(encoding='utf-8')
questions=json.loads((root/'data/questions.json').read_text(encoding='utf-8'))
checks={
 'release_manifest':manifest.get('release')=='Sprint 85' and manifest.get('version')=='1.0.85' and manifest.get('latest_sprint')==85,
 'api_release':'RELEASE = "85.0.0"' in api,
 'module_injected':'sprint85_account_completion.css' in app and 'sprint85_account_completion.js' in app,
 'confirmation_action':'تأكيد إنشاء الحساب' in js and 's85-setup-confirm' in css,
 'navigation_lock':'s85-onboarding-lock' in css and "target!=='studentSetupPage'" in js,
 'profile_avatar_continuity':'s54_profile_${userId()}' in js and 'suhail:profile-saved' in js,
 'compact_typography':'--s85-body:12px' in css and '--s85-title:20px' in css,
 'question_scaling_preserved':'var(--s80-font-question)' in css and 'var(--s80-font-choice)' in css,
 'fast_wheel':'2.55' in js and "addEventListener('wheel'" in js and 'stopImmediatePropagation' in js,
 'scrollbars_hidden':'scrollbar-width:none' in css and '::-webkit-scrollbar' in css,
 'question_count':len(questions)==5400,
}
py_compile.compile(str(root/'app.py'),doraise=True)
node=subprocess.run(['node','--check',str(root/'src/ui/sprint85_account_completion.js')],capture_output=True,text=True)
checks['javascript_syntax']=node.returncode==0
report={'release':'85.0.0','passed':all(checks.values()),'checks':checks,'question_count':len(questions)}
out=root/'docs/reports/SPRINT_85_CHECKS.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
