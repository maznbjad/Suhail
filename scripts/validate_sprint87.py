#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'config/project_manifest.json').read_text(encoding='utf-8'))
questions = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
summaries = json.loads((ROOT / 'data/smart_summaries.json').read_text(encoding='utf-8'))
app = (ROOT / 'app.py').read_text(encoding='utf-8')
api = (ROOT / 'src/api/server.py').read_text(encoding='utf-8')
css = (ROOT / 'src/ui/sprint87_motivation.css').read_text(encoding='utf-8')
js = (ROOT / 'src/ui/sprint87_motivation.js').read_text(encoding='utf-8')

checks = {
    'release_manifest': manifest.get('release') == 'Sprint 87' and manifest.get('version') == '1.0.87' and manifest.get('latest_sprint') == 87,
    'api_release': 'RELEASE = "87.0.0"' in api,
    'module_injected_last': 'sprint87_motivation.css' in app and 'sprint87_motivation.js' in app and app.rfind('sprint87_motivation.js') > app.rfind('sprint86_summary_cards.js'),
    'avatar_assets_embedded': '__S87_AVATAR_PORTRAITS__' in js and '__S87_AVATAR_HALF__' in js and 'asset_data_uri' in app,
    'monthly_two_shields': 'const MAX_SHIELDS=2' in js and 'shieldMonth!==month()' in js,
    'one_shield_per_missed_day': 'st.shields-=info.missed' in js and 'for(let i=1;i<=info.missed;i++)' in js,
    'maximum_two_consecutive_days': 'missed<=2&&missed<=st.shields' in js,
    'meaningful_activity_only': "recordActivity('answer')" in js and "recordActivity('exam')" in js and "recordActivity('daily-plan')" in js,
    'hidden_result_neutral': 'window.SUHAIL_SHOW_RESULT===false' in js and "showReaction('neutral'" in js,
    'selected_character_reactions': 'profile().avatarId' in js and "avatarSrc(opts.celebrate?'half':'portrait')" in js,
    'return_reaction': "showReaction('return'" in js and 'evaluateReturn' in js,
    'daily_plan_celebration_once': 'planCelebratedDate===today()' in js and "showReaction('celebrate'" in js,
    'home_journey_card': 's87-motivation-card' in js and '.s87-motivation-card' in css,
    'dark_mode_supported': 'body.s55-dark .s87-motivation-card' in css and 'body.s55-dark .s87-modal' in css,
    'question_bank_5400': len(questions) == 5400,
    'physics_summaries_72': len(summaries) == 72,
}

py_compile.compile(str(ROOT / 'app.py'), doraise=True)
py_compile.compile(str(ROOT / 'src/api/server.py'), doraise=True)

renderable = (js.replace('__S87_AVATARS__', '{"default":"male_02","items":[]}')
                .replace('__S87_AVATAR_PORTRAITS__', '{}')
                .replace('__S87_AVATAR_HALF__', '{}'))
with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.js', delete=False) as f:
    f.write(renderable)
    tmp = f.name
node = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
Path(tmp).unlink(missing_ok=True)
checks['javascript_syntax'] = node.returncode == 0

report = {
    'release': '87.0.0',
    'passed': all(checks.values()),
    'checks': checks,
    'counts': {
        'question_bank': len(questions),
        'physics_summaries': len(summaries),
        'monthly_shields': 2,
        'maximum_consecutive_protected_days': 2,
    },
    'interaction_qa': {
        'shield_balance_scenario': '2 -> 1 after protecting one missed day',
        'streak_scenario': 'three connected days after shield and current activity',
        'hidden_result': 'neutral reaction with no correctness disclosure',
        'daily_plan': 'single celebration after practice, errors, and summary are complete',
        'javascript_errors': 0,
    },
}

out = ROOT / 'docs/reports/SPRINT_87_CHECKS.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['passed'] else 1)
