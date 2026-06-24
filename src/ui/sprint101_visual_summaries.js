/* Suhail Sprint 101 — visual full-screen physics and chemistry summaries. */
(function(){
  'use strict';
  const VERSION='101.0.0';
  const VISUALS=__S101_VISUALS__;
  const BACK='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const rawBank=()=>{try{return Array.isArray(window.smartSummaries)?window.smartSummaries:(typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries:[])}catch(_){return[]}};
  const page=()=>document.getElementById('summariesPage');
  const state={view:'gateway',subject:'',stage:'',unit:'',summaryId:'',reference:null,example:0,question:0,answers:{},query:''};
  const preferred={
    'فيزياء':['فيزياء 1','فيزياء 2','فيزياء 3-1','فيزياء 3-2'],
    'كيمياء':['كيمياء 1','كيمياء 2-1','كيمياء 2-2','كيمياء 3']
  };
  function subjectBank(subject){return rawBank().filter(x=>String(x.subject||'').trim()===subject&&x.learning_path_v2);}
  function byId(id){return rawBank().find(x=>String(x.summary_id||x.id)===String(id))||null;}
  function stages(subject){const found=[...new Set(subjectBank(subject).map(x=>String(x.stage||'').trim()).filter(Boolean))];const p=preferred[subject]||[];return [...p.filter(x=>found.includes(x)),...found.filter(x=>!p.includes(x))];}
  function units(subject,stage){const map=new Map();subjectBank(subject).filter(x=>String(x.stage)===String(stage)).forEach(x=>{const u=String(x.unit||'وحدة').trim();if(!map.has(u))map.set(u,[]);map.get(u).push(x)});return [...map.entries()].map(([unit,items])=>({unit,items:items.sort((a,b)=>(a.order||0)-(b.order||0))}));}
  function unitItems(subject,stage,unit){return subjectBank(subject).filter(x=>String(x.stage)===String(stage)&&String(x.unit)===String(unit)).sort((a,b)=>(a.order||0)-(b.order||0));}
  function activate(detail=false){const p=page();if(!p)return null;document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x===p));p.className=`page active s101-active${detail?' s101-detail':''}`;document.body.classList.add('s101-summary-active');return p;}
  function leave(){document.body.classList.remove('s101-summary-active');const p=page();if(p)p.classList.remove('s101-active','s101-detail');}
  function top(title,subtitle,back){return `<div class="s101-top"><button class="s101-back" type="button" data-s101-back="${esc(back)}" aria-label="رجوع">${BACK}</button><div class="s101-top-copy"><b>${esc(title)}</b><span>${esc(subtitle||'')}</span></div><span></span></div>`;}
  function shell(content,detail=false){return `<div class="s101-page${detail?' s101-page-detail':''}"><div class="s101-shell">${content}</div></div>`;}
  function menu(title,subtitle,badge,action){return `<button class="s101-menu" type="button" data-s101-action="${esc(action)}"><span><b>${esc(title)}</b><small>${esc(subtitle)}</small></span><em>${esc(badge||'فتح')}</em></button>`;}
  function bindCommon(root){
    root.querySelectorAll('[data-s101-back]').forEach(b=>b.addEventListener('click',()=>dispatch(b.dataset.s101Back)));
    root.querySelectorAll('[data-s101-action]').forEach(b=>b.addEventListener('click',()=>dispatch(b.dataset.s101Action)));
  }
  function dispatch(action){
    const [name,...args]=String(action||'').split('::').map(decodeURIComponent);
    if(name==='home'){leave();window.showPage?.('homePage');}
    else if(name==='gateway')renderGateway();
    else if(name==='tahsili')renderSubjects();
    else if(name==='subject')renderStages(args[0]);
    else if(name==='stage')renderUnits(args[0],args[1]);
    else if(name==='unit')renderLessons(args[0],args[1],args[2]);
    else if(name==='lesson')openLesson(args[0]);
    else if(name==='empty')renderEmpty(args[0]);
  }
  function renderGateway(){state.view='gateway';const p=activate();if(!p)return;p.innerHTML=shell(`${top('الملخصات','مراجعة بصرية سريعة وواضحة','home')}<div class="s101-list-wrap"><div class="s101-list-heading"><h2>اختر مسارك</h2><p>تفتح المادة ثم الكتاب والوحدة والدرس.</p></div><div class="s101-list">${menu('تحصيلي','الفيزياء والكيمياء، ثم الرياضيات والأحياء وعلم البيئة',`${subjectBank('فيزياء').length+subjectBank('كيمياء').length} ملخص`,'tahsili')}${menu('قدرات كمي','الملخصات قيد الإعداد','قريبًا','empty::قدرات كمي')}${menu('قدرات لفظي','الملخصات قيد الإعداد','قريبًا','empty::قدرات لفظي')}</div></div>`);bindCommon(p);p.scrollTop=0;}
  function renderSubjects(){state.view='subjects';const p=activate();if(!p)return;const rows=[
    ['فيزياء','أربعة كتب وملخصات بصرية مرتبطة بالأسئلة',`${subjectBank('فيزياء').length} درس`,'subject::فيزياء'],
    ['كيمياء','أربعة كتب مبنية من المناهج المرفوعة',`${subjectBank('كيمياء').length} درس`,'subject::كيمياء'],
    ['رياضيات','سيظهر بعد استلام المنهج واعتماده','غير منشور','empty::رياضيات'],
    ['أحياء','سيكون قسمًا مستقلًا داخل الملخصات','غير منشور','empty::أحياء'],
    ['علم البيئة','قسم مستقل في الملخصات، ومشترك مع الأحياء في الاختبار','غير منشور','empty::علم البيئة']
  ];p.innerHTML=shell(`${top('مواد التحصيلي','اختر المادة التي تريد مراجعتها','gateway')}<div class="s101-list-wrap"><div class="s101-list">${rows.map(r=>menu(...r)).join('')}</div></div>`);bindCommon(p);p.scrollTop=0;}
  function renderStages(subject){state.view='stages';state.subject=subject;const p=activate();if(!p)return;const rows=stages(subject).map(st=>{const us=units(subject,st),n=us.reduce((a,x)=>a+x.items.length,0);return menu(st,`${us.length} فصول أو وحدات مرتبة`,`${n} درس`,`stage::${encodeURIComponent(subject)}::${encodeURIComponent(st)}`)});p.innerHTML=shell(`${top(subject,'اختر الكتاب المناسب لك','tahsili')}<div class="s101-list-wrap"><div class="s101-list">${rows.join('')}</div></div>`);bindCommon(p);p.scrollTop=0;}
  function renderUnits(subject,stage){state.view='units';state.subject=subject;state.stage=stage;const p=activate();if(!p)return;const all=units(subject,stage);const q=String(state.query||'').trim().toLowerCase();const filtered=q?all.filter(x=>(x.unit+' '+x.items.map(i=>i.title).join(' ')).toLowerCase().includes(q)):all;p.innerHTML=shell(`${top(stage,subject,`subject::${encodeURIComponent(subject)}`)}<div class="s101-list-wrap"><label class="s101-search"><input id="s101Search" placeholder="ابحث باسم الوحدة أو الدرس" value="${esc(state.query)}"></label><div class="s101-list">${filtered.map(x=>menu(x.unit,(x.items[0]?.simple_idea||'').slice(0,110),`${x.items.length} دروس`,`unit::${encodeURIComponent(subject)}::${encodeURIComponent(stage)}::${encodeURIComponent(x.unit)}`)).join('')}</div>${filtered.length?'':'<div class="s101-empty">لا توجد نتيجة مطابقة.</div>'}</div>`);bindCommon(p);const input=p.querySelector('#s101Search');if(input)input.addEventListener('input',()=>{state.query=input.value;renderUnits(subject,stage);setTimeout(()=>page()?.querySelector('#s101Search')?.focus(),0)});p.scrollTop=0;}
  function renderLessons(subject,stage,unit){state.view='lessons';state.subject=subject;state.stage=stage;state.unit=unit;const p=activate();if(!p)return;const items=unitItems(subject,stage,unit);p.innerHTML=shell(`${top(unit,`${stage} • ${items.length} دروس`,`stage::${encodeURIComponent(subject)}::${encodeURIComponent(stage)}`)}<div class="s101-list-wrap"><div class="s101-list">${items.map((s,i)=>menu(`${i+1}. ${s.title}`,(s.simple_idea||s.summary||'').slice(0,115),s.linked_question_count?`${s.linked_question_count} سؤال مرتبط`:'ملخص بصري',`lesson::${encodeURIComponent(s.summary_id||s.id)}`)).join('')}</div></div>`);bindCommon(p);p.scrollTop=0;}
  function renderEmpty(title){const p=activate();if(!p)return;p.innerHTML=shell(`${top(title,'المحتوى غير منشور بعد','tahsili')}<div class="s101-empty">سيظهر هذا القسم بعد استلام المنهج وبنائه بالقالب البصري المعتمد.</div>`);bindCommon(p);p.scrollTop=0;}
  function normalize(summary){
    const lp=summary.learning_path_v2||{};
    const fz=lp.from_zero;
    const idea=typeof fz==='object'&&!Array.isArray(fz)?(fz.text||summary.simple_idea||summary.summary||''):(Array.isArray(fz)?fz.filter(Boolean).join(' '):(summary.simple_idea||summary.summary||''));
    const why=typeof fz==='object'&&!Array.isArray(fz)?(fz.why||summary.links_back||''):(summary.links_back||summary.scientific_links?.[0]||'');
    const defs=(lp.definitions||summary.definitions||[]).slice(0,5);
    const formulas=lp.formula_cards||summary.formula_cards||summary.laws||[];
    const examples=lp.worked_examples||summary.worked_examples||[];
    const confuse=lp.dont_confuse||summary.dont_confuse||[];
    const traps=lp.common_traps||summary.common_mistakes||[];
    const patterns=lp.exam_patterns||summary.exam_patterns||summary.test_ideas||[];
    const qs=lp.practice_questions||summary.practice_questions||[];
    const tk=lp.takeaway||{};
    return {lp,idea,why,defs,formulas,examples,confuse,traps,patterns,qs,takeaway:{idea:tk.idea||tk.main_idea||summary.simple_idea||'',formula:tk.formula||tk.main_rule||formulas[0]?.formula||summary.core_rule||'',trap:tk.trap||tk.main_trap||traps[0]||''}};
  }
  function card(cls,title,body){return `<section class="s101-card ${cls}"><h3>${esc(title)}</h3>${body}</section>`;}
  function defBody(defs){return `<ul>${defs.slice(0,3).map(x=>`<li><b>${esc(x.term||x.title||'')}</b>: ${esc(x.meaning||x.description||'')}</li>`).join('')}</ul>`;}
  function listText(list){return `<p>${esc((list||[]).map(x=>typeof x==='string'?x:(x.explanation||x.description||x.text||x.title||'')).filter(Boolean).slice(0,2).join(' '))}</p>`;}
  function referenceBox(summary){const r=state.reference;if(!r||String(r.summary_id)!==String(summary.summary_id||summary.id))return'';const blocks=summary.knowledge_blocks||[];const b=blocks.find(x=>String(x.block_id||x.id)===String(r.block_id));return b?`<div class="s101-reference" id="s101Reference"><small>وصلت من سؤال مرتبط</small><b>${esc(b.title||summary.title)}</b><span>${esc(b.content||'')}</span></div>`:'';}
  function lawSection(n){const f=n.formulas[0];if(!f)return'';return `<section class="s101-full" id="s101Law"><div class="s101-section-head"><div><b>${esc(f.title||'القانون أو القاعدة الأساسية')}</b><span>المعنى أولًا، ثم العلاقة</span></div><em class="s101-pill">قانون</em></div><div class="s101-formula">${esc(f.formula||f.meaning||'')}</div><p class="s101-law-text">${esc(f.meaning||f.when_to_use||'')}</p>${f.common_error?`<div class="s101-law-note"><b>انتبه:</b> ${esc(f.common_error)}</div>`:''}</section>`;}
  function exampleSection(n){if(!n.examples.length)return'';state.example=Math.min(state.example,n.examples.length-1);const e=n.examples[state.example]||n.examples[0];return `<section class="s101-full" id="s101Examples"><div class="s101-section-head"><div><b>أمثلة محلولة</b><span>مثال واحد واضح في كل مرة</span></div><em class="s101-pill">${esc(e.level||'مثال')}</em></div><div class="s101-example-tabs">${n.examples.map((x,i)=>`<button class="s101-example-tab ${i===state.example?'active':''}" data-s101-example="${i}">${esc(x.level||`مثال ${i+1}`)}</button>`).join('')}</div><div class="s101-example-body"><h4>${esc(e.title||'مثال تطبيقي')}</h4><p><b>السؤال:</b> ${esc(e.problem||'')}</p><p><b>لماذا هذه الطريقة؟</b> ${esc(e.why_this_method||'')}</p><div class="s101-steps">${(e.steps||[]).map((s,i)=>`<div class="s101-step">${i+1}. ${esc(s)}</div>`).join('')}</div><div class="s101-answer"><b>النتيجة:</b> ${esc(e.answer||'')}</div></div></section>`;}
  function quizSection(n){if(!n.qs.length)return'';state.question=Math.min(state.question,n.qs.length-1);const qi=state.question,q=n.qs[qi],ans=state.answers[qi];return `<section class="s101-full" id="s101Quiz"><div class="s101-section-head"><div><b>اختبر فهمك</b><span>الإتقان من 4 إجابات صحيحة من 5</span></div><em class="s101-pill">${qi+1}/${n.qs.length}</em></div><div class="s101-question">${esc(q.question||'')}</div><div class="s101-options">${(q.options||[]).map((o,i)=>`<button class="s101-option ${ans!==undefined?(i===q.correct_index?'correct':i===ans?'wrong':''):''}" data-s101-answer="${i}" ${ans!==undefined?'disabled':''}>${esc(o)}</button>`).join('')}</div>${ans!==undefined?`<div class="s101-explain">${esc(q.explanation||'')}</div>`:''}<div class="s101-quiz-nav"><button data-s101-qnav="prev" ${qi===0?'disabled':''}>السابق</button><div class="s101-dots">${n.qs.map((_,i)=>`<i class="${i===qi?'active':''} ${state.answers[i]!==undefined?'done':''}"></i>`).join('')}</div><button class="primary" data-s101-qnav="next" ${qi===n.qs.length-1?'disabled':''}>التالي</button></div></section>`;}
  function detailNav(summary){const items=unitItems(summary.subject,summary.stage,summary.unit),i=items.findIndex(x=>String(x.summary_id||x.id)===String(summary.summary_id||summary.id));const prev=items[i-1],next=items[i+1];return `<div class="s101-text-nav">${prev?`<button data-s101-open="${esc(prev.summary_id||prev.id)}">الدرس السابق</button>`:'<span></span>'}${next?`<button class="primary" data-s101-open="${esc(next.summary_id||next.id)}">الدرس التالي</button>`:'<span></span>'}</div>`;}
  function renderLesson(summary,preserve=false){const p=activate(true);if(!p||!summary)return;state.view='detail';state.subject=summary.subject;state.stage=summary.stage;state.unit=summary.unit;state.summaryId=String(summary.summary_id||summary.id);const n=normalize(summary);const img=VISUALS[summary.visual_id]||VISUALS[summary.learning_path_v2?.visual_id]||'';const visual=img?`<figure class="s101-visual"><img src="${img}" alt="رسم تعليمي لدرس ${esc(summary.title)}"><figcaption>رسم تعليمي مبسط صُنع خصيصًا للدرس</figcaption></figure>`:'';const html=`<div class="s101-page s101-page-detail"><div class="s101-shell"><div class="s101-detail-inner">${top('ملخص الدرس',`${summary.stage} • ${summary.unit}`,`unit::${encodeURIComponent(summary.subject)}::${encodeURIComponent(summary.stage)}::${encodeURIComponent(summary.unit)}`)}<header class="s101-hero"><h1>${esc(summary.title)}</h1><p>${esc(n.idea)}</p><i class="s101-accent"></i></header>${referenceBox(summary)}${visual}<div class="s101-grid">${card('idea','الفكرة الأساسية',`<p>${esc(n.idea)}</p>`)}${card('why','لماذا يحدث؟',`<p>${esc(n.why)}</p>`)}${card('defs','التعريفات',defBody(n.defs))}${card('compare','لا تخلط',listText(n.confuse))}${card('trap','الفخ الشائع',listText(n.traps))}${card('exam','كيف يأتي في التحصيلي؟',listText(n.patterns))}</div>${lawSection(n)}${exampleSection(n)}${quizSection(n)}<section class="s101-full"><div class="s101-section-head"><div><b>الخلاصة</b><span>ما يجب أن يبقى معك</span></div><em class="s101-pill">جاهز للمراجعة</em></div><div class="s101-takeaway"><div><b>الفكرة</b><span>${esc(n.takeaway.idea)}</span></div><div><b>القانون</b><span>${esc(n.takeaway.formula)}</span></div><div><b>الفخ</b><span>${esc(n.takeaway.trap)}</span></div></div></section>${detailNav(summary)}</div></div></div>`;const y=preserve?p.scrollTop:0;p.innerHTML=html;bindCommon(p);bindDetail(p,summary,n);p.scrollTop=y;if(state.reference)setTimeout(()=>p.querySelector('#s101Reference')?.scrollIntoView({behavior:'smooth',block:'center'}),100);}
  function bindDetail(root,summary,n){root.querySelectorAll('[data-s101-example]').forEach(b=>b.addEventListener('click',()=>{state.example=Number(b.dataset.s101Example)||0;renderLesson(summary,true)}));root.querySelectorAll('[data-s101-answer]').forEach(b=>b.addEventListener('click',()=>{if(state.answers[state.question]!==undefined)return;state.answers[state.question]=Number(b.dataset.s101Answer);renderLesson(summary,true)}));root.querySelectorAll('[data-s101-qnav]').forEach(b=>b.addEventListener('click',()=>{state.question=Math.max(0,Math.min(n.qs.length-1,state.question+(b.dataset.s101Qnav==='next'?1:-1)));renderLesson(summary,true)}));root.querySelectorAll('[data-s101-open]').forEach(b=>b.addEventListener('click',()=>openLesson(b.dataset.s101Open)));}
  function openLesson(id,reference=null){const s=byId(id);if(!s)return;state.example=0;state.question=0;state.answers={};state.reference=reference;renderLesson(s,false);}
  function openReference(r){if(!r)return;const sid=r.summary_id||r.summary?.summary_id||r.summary?.id;const bid=r.block_id||r.block?.block_id||r.block?.id;openLesson(sid,{summary_id:sid,block_id:bid});}
  function install(){
    const oldShow=window.showPage;
    if(typeof oldShow==='function'){window.showPage=function(id){const out=oldShow.apply(this,arguments);if(id==='summariesPage')setTimeout(renderGateway,145);else leave();return out;};}
    window.s101OpenGateway=renderGateway;window.s101OpenSubject=renderStages;window.s101OpenLesson=openLesson;window.s101OpenReference=openReference;
    window.s71OpenGateway=renderGateway;window.s71OpenExam=e=>String(e)==='تحصيلي'?renderSubjects():renderEmpty(e);window.s71OpenSubject=renderStages;window.s71OpenStage=stage=>renderUnits(state.subject||'فيزياء',stage);window.s71OpenUnit=(stage,unit)=>renderLessons(state.subject||'فيزياء',stage,unit);
    window.s79OpenReference=openReference;window.s86OpenReference=openReference;window.s79OpenLesson=openLesson;window.s86OpenLesson=openLesson;
    window.openSummariesHome=renderGateway;window.openSummaryExam=e=>String(e)==='تحصيلي'?renderSubjects():renderEmpty(e);window.openSummarySubject=renderStages;
    window.SuhailSummaries101={version:VERSION,state,renderGateway,renderSubjects,renderStages,renderUnits,renderLessons,openLesson,openReference,leave};
    window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
