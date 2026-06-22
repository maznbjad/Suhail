import json, re, sqlite3, pathlib, copy, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUM_PATH = ROOT/'data'/'smart_summaries.json'
Q_PATH = ROOT/'data'/'questions.json'
DB_PATH = ROOT/'data'/'suhail_learning.db'
OUT_MAP = ROOT/'data'/'content'/'summary_knowledge_map.json'
OUT_SCHEMA = ROOT/'data'/'content'/'knowledge_link_schema.json'
REPORT = ROOT/'docs'/'reports'/'SPRINT_69_SUMMARY_LINKING_REPORT.json'

AR_DIAC = re.compile(r'[\u064B-\u065F\u0670]')
NONWORD = re.compile(r'[^\u0600-\u06FFa-zA-Z0-9]+')

def norm(v):
    s = str(v or '').normalize('NFKD') if hasattr(str(v or ''), 'normalize') else str(v or '')
    # Python str has no normalize; use unicodedata
    import unicodedata
    s = unicodedata.normalize('NFKD', str(v or ''))
    s = AR_DIAC.sub('', s)
    s = s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي')
    s = NONWORD.sub(' ', s).strip().lower()
    return s

def slug(v):
    s = norm(v).replace(' ','_')
    return s[:80] or 'block'

def uniq(seq):
    out=[]; seen=set()
    for x in seq:
        x=str(x or '').strip()
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def add_block(blocks, summary, btype, title, content, keywords, order, core=False):
    content=str(content or '').strip()
    if not content:
        return None
    seq = 1 + sum(1 for b in blocks if b['type']==btype)
    bid = f"PHY-{int(summary['order']):03d}-{btype.upper()}-{seq:02d}"
    block={
        'id': bid,
        'summary_id': summary['id'],
        'subject': 'فيزياء',
        'stage': summary.get('stage',''),
        'unit': summary.get('unit',''),
        'lesson': summary.get('title',''),
        'type': btype,
        'title': str(title or '').strip(),
        'content': content,
        'keywords': uniq(list(summary.get('keywords') or []) + list(keywords or []) + [title, summary.get('title'), summary.get('unit')]),
        'order': order,
        'is_core': bool(core),
        'search_text': norm(' '.join(uniq([title, content] + list(keywords or []) + list(summary.get('keywords') or []))))
    }
    blocks.append(block)
    return block

summaries=json.loads(SUM_PATH.read_text(encoding='utf-8'))
all_blocks=[]
for s in summaries:
    s['summary_id']=s.get('summary_id') or s['id']
    blocks=[]
    idx=10
    add_block(blocks,s,'idea','الفكرة الجوهرية',s.get('simple_idea'),['فكرة','جوهر'],idx,True); idx+=10
    for c in s.get('concept_map') or []:
        add_block(blocks,s,'definition',c.get('title'),c.get('description'),[c.get('title'),'تعريف'],idx,True); idx+=10
    add_block(blocks,s,'rule','القانون أو القاعدة الأساسية',s.get('core_rule'),['قانون','قاعدة','علاقة'],idx,True); idx+=10
    rel=(s.get('essence_buttons') or {}).get('relationship')
    add_block(blocks,s,'relationship','العلاقة المهمة',rel,['علاقة','طردية','عكسية'],idx,False); idx+=10
    trap=(s.get('essence_buttons') or {}).get('trap')
    add_block(blocks,s,'trap','الفخ الشائع',trap,['فخ','خطأ شائع','لا تخلط'],idx,True); idx+=10
    add_block(blocks,s,'tip','تلميح سهيل',s.get('simple_back'),['تلميح سهيل','اختصار'],idx,False); idx+=10
    if s.get('links_back') and s.get('links_back')!=s.get('simple_back'):
        add_block(blocks,s,'tip','كيف تفكر في السؤال؟',s.get('links_back'),['تلميح','تفكير'],idx,False); idx+=10
    ex=s.get('example') or {}
    add_block(blocks,s,'example',ex.get('title') or 'مثال',ex.get('text'),['مثال','تطبيق'],idx,False); idx+=10
    for row in s.get('comparison') or []:
        txt=' — '.join([str(row.get('case') or '').strip(),str(row.get('effect') or '').strip(),str(row.get('example') or '').strip()]).strip(' —')
        add_block(blocks,s,'comparison',row.get('case') or 'مقارنة',txt,['مقارنة','لا تخلط'],idx,False); idx+=10
    s['knowledge_blocks']=blocks
    s['knowledge_block_count']=len(blocks)
    all_blocks.extend(blocks)

# Skill -> curated summary order
SKILL_ORDER={
'القياس':2,'دقة القياس':2,'المسافة':4,'الإزاحة':4,'السرعة المتجهة':6,'السرعة المنتظمة':6,
'التسارع':7,'التسارع المنتظم':8,'مساحة منحنى السرعة-الزمن':8,
'قانون نيوتن الأول':11,'قانون نيوتن الثاني':11,'قانون نيوتن الثالث':11,
'القوة المركزية':17,'اتجاه القوة المركزية':17,'عزم القوة':22,'قوة الجاذبية':20,
'الزخم الخطي':24,'الشغل':26,'الطاقة الحركية':28,'القدرة':26,
'الموجة الميكانيكية':37,'سرعة الموجة':37,'التردد':36,'العلاقة بين التردد والدور':36,
'شدة الصوت':39,'الانعكاس':43,'قانون الانعكاس':43,'الانكسار':45,
'شدة التيار الكهربائي':54,'شدة التيار':54,'فرق الجهد':54,'المقاومة الكهربائية':54,'قانون أوم':54,
'مقاومات على التوالي':57,'المجال المغناطيسي':58,'التأثير الكهروضوئي':64,'الانشطار النووي':71,
}
UNIT_ORDER={'القياس':2,'الحركة':6,'القوى':11,'الحركة الدائرية':17,'الجاذبية':20,'الدوران':22,'الزخم':24,'الشغل والطاقة':26,'الموجات':37,'الصوت':39,'الضوء':43,'الكهرباء':54,'المغناطيسية':58,'الفيزياء الحديثة':64,'الفيزياء النووية':71}
BY_ORDER={int(s['order']):s for s in summaries}

def choose_summary(q):
    sk=str(q.get('skill') or '').strip(); un=str(q.get('unit') or '').strip()
    n=SKILL_ORDER.get(sk) or UNIT_ORDER.get(un)
    if n in BY_ORDER: return BY_ORDER[n]
    raw=norm(' '.join([sk,un,q.get('question','')])); best=None; score=-1
    for s in summaries:
        terms=uniq([s.get('title'),s.get('unit')]+list(s.get('keywords') or []))
        sc=sum(3 if norm(t)==norm(sk) else 1 for t in terms if norm(t) and norm(t) in raw)
        if sc>score: best=s; score=sc
    return best

def choose_block(s,q):
    blocks=s.get('knowledge_blocks') or []
    sk=norm(q.get('skill')); text=norm(q.get('question'))
    # exact definition first
    for b in blocks:
        if b['type']=='definition' and (norm(b['title'])==sk or sk in norm(b['title']) or norm(b['title']) in sk):
            return b
    misconception=str(q.get('misconception_id') or '').strip()
    if misconception:
        traps=[b for b in blocks if b['type']=='trap']
        if traps: return traps[0]
    numerical=('كم','احسب','اوجد','قانون','يساوي','مقدار','سرعة','تسارع','قوة','زخم','شغل','طاقة','قدرة','تيار','جهد','مقاومة')
    if any(x in text for x in numerical):
        rules=[b for b in blocks if b['type']=='rule']
        if rules: return rules[0]
    ideas=[b for b in blocks if b['type']=='idea']
    return ideas[0] if ideas else (blocks[0] if blocks else None)

questions=json.loads(Q_PATH.read_text(encoding='utf-8'))
linked=0; block_counts=collections.Counter(); summary_counts=collections.Counter(); unlinked=[]
for q in questions:
    if q.get('subject')!='فيزياء':
        continue
    s=choose_summary(q); b=choose_block(s,q) if s else None
    if not s or not b:
        unlinked.append(q.get('public_id')); continue
    q['summary_id']=s['summary_id']
    q['summary_exam']='تحصيلي'
    q['summary_subject']='فيزياء'
    q['summary_stage']=s.get('stage','')
    q['summary_unit']=s.get('unit','')
    q['summary_title']=s.get('title','')
    q['summary_block_id']=b['id']
    q['summary_block_type']=b['type']
    q['summary_block_title']=b['title']
    q['summary_block_excerpt']=b['content'][:240]
    q['knowledge_link_status']='linked_auto_curated_v1'
    linked+=1; block_counts[b['id']]+=1; summary_counts[s['summary_id']]+=1

SUM_PATH.write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
Q_PATH.write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
OUT_MAP.parent.mkdir(parents=True,exist_ok=True)
OUT_MAP.write_text(json.dumps({
    'version':'69.0.0','subject':'فيزياء','summary_count':len(summaries),'block_count':len(all_blocks),
    'summaries':[{'summary_id':s['summary_id'],'stage':s.get('stage'),'unit':s.get('unit'),'title':s.get('title'),'block_ids':[b['id'] for b in s.get('knowledge_blocks',[])]} for s in summaries],
    'blocks':all_blocks
},ensure_ascii=False,indent=2),encoding='utf-8')
OUT_SCHEMA.write_text(json.dumps({
    'version':'69.0.0','entity':'question_summary_link','required':['summary_id','summary_block_id','summary_subject','summary_unit','summary_title','summary_block_title'],
    'rules':{'max_primary_blocks_per_question':1,'secondary_blocks_optional':True,'deep_link_exact_block':True,'student_visible_keywords':False,'admin_editable':True}
},ensure_ascii=False,indent=2),encoding='utf-8')

# Rebuild question payloads in SQLite
con=sqlite3.connect(DB_PATH)
with con:
    con.execute('DELETE FROM questions')
    con.executemany('INSERT INTO questions(id,exam,category,skill,subject,unit,difficulty,payload_json) VALUES(?,?,?,?,?,?,?,?)',[
        (q['id'],q.get('exam',''),q.get('category',''),q.get('skill',''),q.get('subject',''),q.get('unit',''),q.get('difficulty',''),json.dumps(q,ensure_ascii=False,separators=(',',':'))) for q in questions
    ])
con.close()

REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps({
    'version':'69.0.0','physics_summaries':len(summaries),'knowledge_blocks':len(all_blocks),'physics_questions':sum(1 for q in questions if q.get('subject')=='فيزياء'),
    'linked_physics_questions':linked,'unlinked_physics_questions':unlinked,
    'block_type_counts':dict(collections.Counter(b['type'] for b in all_blocks)),
    'top_linked_summaries':summary_counts.most_common(20),'top_linked_blocks':block_counts.most_common(20)
},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'summaries':len(summaries),'blocks':len(all_blocks),'linked':linked,'unlinked':len(unlinked)},ensure_ascii=False))
