from __future__ import annotations
from pathlib import Path
import json, sqlite3, sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]

def check(condition,message):
    if not condition: errors.append(message)

summaries=json.loads((ROOT/'data/smart_summaries.json').read_text(encoding='utf-8'))
questions=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
physics=[x for x in summaries if x.get('subject')=='فيزياء']
chem=[x for x in summaries if x.get('subject')=='كيمياء']
chem_q=[x for x in questions if x.get('subject')=='كيمياء' or x.get('category')=='كيمياء']
check(len(summaries)==155,f'expected 155 summaries, found {len(summaries)}')
check(len(physics)==72,f'expected 72 physics summaries, found {len(physics)}')
check(len(chem)==83,f'expected 83 chemistry summaries, found {len(chem)}')
check(len(chem_q)==600,f'expected 600 chemistry questions, found {len(chem_q)}')
check(all(q.get('summary_id') and q.get('summary_block_id') for q in chem_q),'some chemistry questions are not linked')
ids={x.get('summary_id') or x.get('id') for x in summaries}
check(all(q.get('summary_id') in ids for q in chem_q),'some chemistry links point to missing summaries')
check(all((ROOT/(x.get('visual_asset') or '')).exists() for x in summaries),'some summary visual assets are missing')
check(all(len(x.get('practice_questions') or [])>=5 for x in chem),'some chemistry lessons have fewer than five internal questions')
check(all(len(x.get('worked_examples') or [])>=3 for x in chem),'some chemistry lessons have fewer than three examples')
check(all(len(x.get('formula_cards') or [])>=1 for x in chem),'some chemistry lessons have no rule/formula card')
check((ROOT/'src/ui/sprint101_visual_summaries.js').exists(),'Sprint 101 JS missing')
check((ROOT/'src/ui/sprint101_visual_summaries.css').exists(),'Sprint 101 CSS missing')
manifest=json.loads((ROOT/'data/chemistry_books_manifest.json').read_text(encoding='utf-8'))
check(manifest.get('book_count')==4,'chemistry manifest must contain four books')
check(manifest.get('lesson_count')==83,'chemistry manifest lesson count mismatch')
with sqlite3.connect(ROOT/'data/suhail_learning.db') as db:
    row=db.execute("select count(*) from questions").fetchone()
    check(row and row[0]==5400,f'SQLite question count mismatch: {row}')

print('Sprint 101 verification')
print(f'  summaries: {len(summaries)} (physics {len(physics)}, chemistry {len(chem)})')
print(f'  questions: {len(questions)} (chemistry linked {sum(bool(q.get("summary_id")) for q in chem_q)}/{len(chem_q)})')
print(f'  visual assets: {len(list((ROOT/"assets/summary_visuals/sprint101").glob("*.webp")))} WebP')
print(f'  chemistry books: {manifest.get("book_count")} / lessons: {manifest.get("lesson_count")}')
if errors:
    for e in errors: print('[FAIL]',e)
    sys.exit(1)
print('[OK] Sprint 101 data, links, visuals and SQLite repository are consistent.')
