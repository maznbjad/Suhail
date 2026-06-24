"""Sprint 108 release validation: PDF books, OCR layers, iPhone containment and source syntax."""
from __future__ import annotations
import json, py_compile, subprocess, tempfile
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
BOOKS={"physics1":18,"physics2":13,"physics31":22}
errors=[];checks={}

def require(cond,msg):
    if not cond: errors.append(msg)

py_compile.compile(str(ROOT/'app.py'),doraise=True)
checks['python_syntax']=True
for name in ['sprint101_visual_summaries.js','sprint102_pdf_reader.js','sprint107_back_button_guard.js']:
    src=(ROOT/'src/ui'/name).read_text(encoding='utf-8')
    src=src.replace('__S101_VISUALS__','{}').replace('__S102_BOOKS__','[]')
    with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
        f.write(src);tmp=f.name
    r=subprocess.run(['node','--check',tmp],capture_output=True,text=True)
    require(r.returncode==0,f'JavaScript syntax failed: {name}: {r.stderr}')
checks['javascript_syntax']=not any('JavaScript syntax' in x for x in errors)

manifest=json.loads((ROOT/'data/content/pdf_books_manifest.json').read_text(encoding='utf-8'))
for key,count in BOOKS.items():
    pdf=ROOT/'assets/summary_pdfs'/f'{key}.pdf'
    images=sorted((ROOT/'assets/summary_pdfs'/key).glob('page_*.webp'))
    ocr=json.loads((ROOT/'assets/summary_pdfs'/f'{key}_ocr.json').read_text(encoding='utf-8'))
    require(pdf.exists(),f'Missing PDF: {key}')
    require(len(fitz.open(pdf))==count,f'PDF page count mismatch: {key}')
    require(len(images)==count,f'Image page count mismatch: {key}')
    require(len(ocr)==count,f'OCR page count mismatch: {key}')
    require(all(len(page)>100 for page in ocr),f'OCR page has insufficient words: {key}')
checks['books']={key:{'pages':count,'ocr_words':sum(len(p) for p in json.loads((ROOT/'assets/summary_pdfs'/f'{key}_ocr.json').read_text(encoding='utf-8')))} for key,count in BOOKS.items()}

app=(ROOT/'app.py').read_text(encoding='utf-8')
require('__S102_BOOKS__' in (ROOT/'src/ui/sprint102_pdf_reader.js').read_text(encoding='utf-8'),'Reader injection placeholder missing')
require('sprint108_ios_ux.css' in app,'Sprint 108 iOS CSS not injected')
require('viewport-fit=cover' in app,'iOS viewport-fit=cover missing')
css=(ROOT/'src/ui/sprint108_ios_ux.css').read_text(encoding='utf-8')
for token in ['safe-area-inset-top','width:44px','padding-top:calc(var(--s108-safe-top) + 64px)','status-bar{display:none']:
    require(token in css,f'Missing iOS UX rule: {token}')
checks['ios_ux_source']=not any('iOS UX' in x for x in errors)

runtime=json.loads((ROOT/'docs/reports/SPRINT_108_RUNTIME_QA.json').read_text(encoding='utf-8'))
d=runtime['desktop'];m=runtime['mobile']
require(d['screen']==d['host']==d['reader'],'Desktop reader is not exactly contained in screen')
require(d['back']['r']<=d['screen']['r'] and d['back']['l']>=d['screen']['l'],'Desktop back control outside screen')
require(d['page']['t']>d['back']['b'],'Back control overlaps first PDF page')
require(runtime.get('paletteVisible') is True and runtime.get('highlights',0)>=1,'Selection/highlight runtime QA failed')
require(m['reader']['l']==0 and m['reader']['t']==0 and m['reader']['w']==390 and m['reader']['h']==844,'Mobile reader does not fill viewport')
checks['runtime_containment']=not errors

out={'version':'108.0.0','ok':not errors,'checks':checks,'errors':errors}
(ROOT/'docs/reports/SPRINT_108_RELEASE_CHECKS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
