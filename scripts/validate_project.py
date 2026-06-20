from pathlib import Path
import json, py_compile
ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT/'app.py', ROOT/'requirements.txt', ROOT/'data/questions.json', ROOT/'data/users.json',
    ROOT/'data/smart_summaries.json', ROOT/'assets/brand', ROOT/'assets/images', ROOT/'assets/sounds'
]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit('Missing: ' + ', '.join(missing))
for p in [ROOT/'data/questions.json', ROOT/'data/users.json', ROOT/'data/smart_summaries.json']:
    json.loads(p.read_text(encoding='utf-8'))
py_compile.compile(str(ROOT/'app.py'), doraise=True)
print('Suhail project validation: OK')
