import fitz, re, json, csv, hashlib, unicodedata, os
from pathlib import Path
ROOT=Path('/mnt/data/s68_work/Suhail_V1_Sprint67')
SOURCES=[
    ('فيزياء', Path('/mnt/data/��كتاب الفيزياء�.pdf')),
    ('كيمياء', Path('/mnt/data/تجميعات الكيمياء 2025.pdf')),
    ('رياضيات', Path('/mnt/data/��كتاب الرياضيات�.pdf')),
    ('الأحياء وعلم البيئة', Path('/mnt/data/كتاب الأحياء وعلم البيئة.pdf')),
]

def clean_line(s):
    s=unicodedata.normalize('NFKC',str(s or ''))
    s=re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]','',s)
    s=re.sub(r'\s+',' ',s).strip()
    return s

def norm(s):
    s=clean_line(s).lower()
    s=re.sub(r'[\u064b-\u065f\u0670]','',s)
    s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي')
    s=re.sub(r'[^\w\u0600-\u06ff?؟]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def is_a(line):
    # A option marker at line start, including Arabic أ when laid out as latin A in these books.
    return bool(re.match(r'^(?:A|Ａ)(?:\s|[:.)-]|(?=[\u0600-\u06ff]))', line)) or line in {'A','Ａ'}

def is_option(line, letter):
    return bool(re.match(rf'^(?:{letter}|{letter.lower()})(?:\s|[:.)-]|(?=[\u0600-\u06ff]))', line)) or line in {letter,letter.lower()}

all_candidates=[]
summary=[]
for subject,path in SOURCES:
    doc=fitz.open(path)
    subject_candidates=[]
    pages_with_candidates=0
    for pno,page in enumerate(doc, start=1):
        raw=page.get_text('text')
        lines=[clean_line(x) for x in raw.splitlines() if clean_line(x)]
        apos=[i for i,l in enumerate(lines) if is_a(l)]
        if apos: pages_with_candidates += 1
        for seq,i in enumerate(apos, start=1):
            prev=apos[seq-2] if seq>1 else -1
            nxt=apos[seq] if seq<len(apos) else len(lines)
            # question statement generally immediately precedes A; include up to 12 lines after prior block.
            before=lines[max(prev+1, i-12):i]
            after=lines[i:min(nxt, i+16)]
            # trim obvious headers/footers
            context=[x for x in before+after if len(x)>0 and not re.search(r'منصة أينشتاين|تجارب طالب|اضغط هنا|قناة|بسم الله|مقدمة',x)]
            text=' | '.join(context)
            key=norm(text)
            if len(key)<8: continue
            subject_candidates.append({
                'subject':subject,'source_file':path.name,'page':pno,'sequence_on_page':seq,
                'raw_context':text[:2000], 'normalized_hash':hashlib.sha256(key.encode()).hexdigest(),
                'status':'source_candidate','publishable':False,'requires_editorial_review':True,
            })
    # exact normalized de-dupe within subject
    seen=set(); unique=[]
    for c in subject_candidates:
        h=c['normalized_hash']
        if h in seen: continue
        seen.add(h); unique.append(c)
    for idx,c in enumerate(unique, start=1):
        c['inventory_id']=f"SRC-{ {'فيزياء':'PHY','كيمياء':'CHEM','رياضيات':'MATH','الأحياء وعلم البيئة':'BIO'}[subject]}-{idx:05d}"
    all_candidates.extend(unique)
    summary.append({
        'subject':subject,'source_file':path.name,'pages':len(doc),
        'raw_a_option_markers':len(subject_candidates),'unique_exact_contexts':len(unique),
        'pages_with_candidates':pages_with_candidates,
    })

outdir=ROOT/'data'/'source_inventory'
outdir.mkdir(parents=True,exist_ok=True)
(outdir/'tahsili_question_candidates.json').write_text(json.dumps(all_candidates,ensure_ascii=False,indent=2),encoding='utf-8')
with open(outdir/'tahsili_question_candidates.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['inventory_id','subject','source_file','page','sequence_on_page','status','publishable','requires_editorial_review','raw_context'])
    w.writeheader(); w.writerows([{k:c.get(k,'') for k in w.fieldnames} for c in all_candidates])
report={
    'method':'A-option marker inventory from embedded PDF text; exact normalized contexts deduplicated. Counts are source candidates, not approved student questions.',
    'sources':summary,
    'raw_candidates':sum(x['raw_a_option_markers'] for x in summary),
    'unique_exact_contexts':len(all_candidates),
    'student_bank_policy':'Only rewritten, independently solved, quality-checked questions are release eligible.',
}
(outdir/'tahsili_inventory_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
