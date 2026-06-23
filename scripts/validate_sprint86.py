#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'config/project_manifest.json').read_text(encoding='utf-8'))
questions = json.loads((ROOT / 'data/questions.json').read_text(encoding='utf-8'))
summaries = json.loads((ROOT / 'data/smart_summaries.json').read_text(encoding='utf-8'))
app = (ROOT / 'app.py').read_text(encoding='utf-8')
api = (ROOT / 'src/api/server.py').read_text(encoding='utf-8')
css = (ROOT / 'src/ui/sprint86_summary_cards.css').read_text(encoding='utf-8')
js = (ROOT / 'src/ui/sprint86_summary_cards.js').read_text(encoding='utf-8')

physics = [s for s in summaries if s.get('subject') == 'فيزياء' and s.get('learning_path_v2')]
linked_physics = [q for q in questions if q.get('exam') == 'تحصيلي' and q.get('subject') == 'فيزياء' and q.get('summary_id') and q.get('summary_block_id')]
all_summary_ids = {str(s.get('summary_id') or s.get('id')) for s in summaries}
all_block_ids = {str(b.get('id')) for s in summaries for b in (s.get('knowledge_blocks') or []) if b.get('id')}

lesson_shape_ok = all(
    len((s.get('learning_path_v2') or {}).get('worked_examples') or []) >= 3
    and len((s.get('learning_path_v2') or {}).get('practice_questions') or []) == 5
    and len((s.get('learning_path_v2') or {}).get('formula_cards') or []) >= 1
    for s in physics
)
links_valid = all(str(q.get('summary_id')) in all_summary_ids and str(q.get('summary_block_id')) in all_block_ids for q in linked_physics)

checks = {
    'release_manifest': manifest.get('release') == 'Sprint 86' and manifest.get('version') == '1.0.86' and manifest.get('latest_sprint') == 86,
    'api_release': 'RELEASE = "86.0.0"' in api,
    'module_injected': 'sprint86_summary_cards.css' in app and 'sprint86_summary_cards.js' in app,
    'paired_card_grid': '.s86-summary-grid' in css and 'grid-template-columns:repeat(2' in css and '.s86-tile[open]{grid-column:1/-1}' in css,
    'laws_next_to_back': 's86-top-actions' in css and 'data-action="back-unit"' in js and 'data-action="open-laws"' in js,
    'laws_removed_from_story_flow': "tile('formulas'" not in js and 'lawsDrawer(summary)' in js,
    'single_example_focus': 'data-example-index' in js and 'state.exampleIndex' in js,
    'single_question_focus': 'state.practiceIndex' in js and 's86-practice-dots' in js,
    'avatar_crop_safe': '#studentSetupPage .s54-avatar-stage img' in css and 'object-fit:contain!important' in css and 'object-position:center bottom!important' in css,
    'physics_lessons_72': len(physics) == 72,
    'lesson_shape_complete': lesson_shape_ok,
    'question_bank_5400': len(questions) == 5400,
    'physics_links_600': len(linked_physics) == 600,
    'physics_links_valid': links_valid,
    'deep_link_override': 'window.s79OpenReference=openReference' in js and 's86-reference-focus' in js,
    'dark_mode_supported': '[data-theme="dark"] #summariesPage .s86-page' in css,
}

py_compile.compile(str(ROOT / 'app.py'), doraise=True)
py_compile.compile(str(ROOT / 'src/api/server.py'), doraise=True)
node = subprocess.run(['node', '--check', str(ROOT / 'src/ui/sprint86_summary_cards.js')], capture_output=True, text=True)
checks['javascript_syntax'] = node.returncode == 0

report = {
    'release': '86.0.0',
    'passed': all(checks.values()),
    'checks': checks,
    'counts': {
        'question_bank': len(questions),
        'physics_lessons': len(physics),
        'physics_exact_links': len(linked_physics),
        'lesson_tiles': 6,
    },
    'design': {
        'top_actions': ['رجوع', 'القوانين'],
        'paired_cards': ['الفكرة من الصفر', 'خريطة الفهم', 'التعريفات الأساسية', 'لا تخلط', 'الفخاخ الشائعة', 'كيف يأتي في التحصيلي؟'],
        'full_width_sections': ['قبل أن تبدأ', 'الأمثلة المحلولة', 'اختبر فهمك', 'خلاصة الدرس'],
        'laws_location': 'drawer opened from the top-left action group beside back',
    },
}

out = ROOT / 'docs/reports/SPRINT_86_CHECKS.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report['passed'] else 1)
