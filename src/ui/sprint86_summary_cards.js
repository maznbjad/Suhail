/* Suhail Sprint 86 — visual two-card summaries and top laws drawer. */
(function(){
  'use strict';
  const VERSION='86.0.0';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const bank=()=>{try{return Array.isArray(window.smartSummaries)?window.smartSummaries:(typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries:[])}catch(_){return[]}};
  const page=()=>document.getElementById('summariesPage');
  const byId=id=>bank().find(s=>String(s.summary_id||s.id)===String(id))||null;
  const physics=()=>bank().filter(s=>String(s.subject||'')==='فيزياء'&&s.learning_path_v2);
  const state={stage:'',unit:'',summaryId:'',answers:{},diagnostic:{},reference:null,practiceIndex:0,exampleIndex:0};
  const safeGet=(key,fallback=null)=>{try{const v=localStorage.getItem(key);return v?JSON.parse(v):fallback}catch(_){return fallback}};
  const safeSet=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch(_){return false}};
  const icons={
    back:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>',
    law:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5z"/><path d="M7 8h2M15 8h2M7 12h2M15 12h2"/></svg>'
  };
  const tileIcons={zero:'✦',map:'↔',definitions:'أ',compare:'⇄',traps:'!',patterns:'▦'};

  function activate(){
    const p=page();if(!p)return null;
    document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x===p));
    p.className='page active';
    document.body.removeAttribute('data-s71-legacy-detail');
    window.SuhailUI70?.update?.();
    return p;
  }
  function progress(summary){
    const key=summary?.learning_path_v2?.mastery?.status_storage_key;
    return key?safeGet(key,{answered:0,correct:0,score:0,mastered:false}):{answered:0,correct:0,score:0,mastered:false};
  }
  function unitItems(stage,unit){return physics().filter(s=>String(s.stage)===String(stage)&&String(s.unit)===String(unit)).sort((a,b)=>(a.order||0)-(b.order||0));}
  function topbar(title,subtitle,showLaws=false){
    return `<div class="s86-topbar"><div class="s86-heading"><b>${esc(title)}</b><span>${esc(subtitle)}</span></div><div class="s86-top-actions"><button class="s86-icon-btn" type="button" data-action="back-unit" aria-label="رجوع">${icons.back}</button>${showLaws?`<button class="s86-law-btn" type="button" data-action="open-laws" aria-label="فتح القوانين">${icons.law}<span>القوانين</span></button>`:''}</div></div>`;
  }
  function previewText(value,fallback='اضغط لعرض التفاصيل'){
    if(Array.isArray(value)){
      const first=value.find(Boolean);
      if(first&&typeof first==='object')return String(first.explanation||first.meaning||first.text||first.title||fallback).slice(0,82);
      return String(first||fallback).slice(0,82);
    }
    return String(value||fallback).slice(0,82);
  }
  function tile(id,title,preview,body,open=false){
    return `<details class="s86-tile" data-section="${esc(id)}" ${open?'open':''}><summary><span class="s86-tile-icon">${tileIcons[id]||'•'}</span><span class="s86-tile-copy"><b>${esc(title)}</b><small>${esc(previewText(preview))}</small></span><span class="s86-tile-toggle">+</span></summary><div class="s86-tile-body">${body}</div></details>`;
  }
  function referenceBox(summary){
    const r=state.reference;if(!r||String(r.summary_id)!==String(summary.summary_id||summary.id))return '';
    const block=(summary.knowledge_blocks||[]).find(b=>String(b.id)===String(r.block_id));
    if(!block)return '';
    return `<section class="s86-reference-focus" data-block-id="${esc(block.id)}"><small>وصلت من سؤال مرتبط</small><b>${esc(block.title||summary.title)}</b><span>${esc(block.content||'')}</span></section>`;
  }
  function diagnosticHtml(q){
    if(!q)return '<div class="s86-explain">ابدأ بقراءة الفكرة من الصفر.</div>';
    const answered=state.diagnostic[state.summaryId];
    return `<div class="s86-diagnostic"><div class="s86-question-text">${esc(q.question)}</div><div class="s86-options">${(q.options||[]).map((o,i)=>`<button class="s86-option ${answered!==undefined?(i===q.correct_index?'correct':i===answered?'wrong':''):''}" type="button" data-diagnostic-option="${i}" ${answered!==undefined?'disabled':''}>${esc(o)}</button>`).join('')}</div>${answered!==undefined?`<div class="s86-explain">${esc(q.explanation||'')}</div>`:''}</div>`;
  }
  function formulasHtml(cards){
    const items=cards||[];
    if(!items.length)return '<div class="s86-explain">لا توجد قوانين مستقلة في هذا الدرس.</div>';
    return items.map(f=>`<article class="s86-formula"><div class="s86-formula-head"><b>${esc(f.title)}</b><span class="s86-chip">${String(f.formula||'').includes('=')?'قانون':'قاعدة'}</span></div><div class="s86-formula-code">${esc(f.formula)}</div><div class="s86-formula-use"><b>متى أستخدمه؟</b> ${esc(f.when_to_use||f.meaning||'')}</div>${(f.symbols||[]).length?`<div class="s86-symbols">${f.symbols.map(s=>`<span><code>${esc(s.symbol)}</code> = ${esc(s.meaning)}${s.unit?` (${esc(s.unit)})`:''}</span>`).join('')}</div>`:''}<div class="s86-formula-warning"><b>متى لا أستخدمه؟</b> ${esc(f.when_not_to_use||'')}</div>${f.common_error?`<div class="s86-formula-warning"><b>الخطأ الشائع:</b> ${esc(f.common_error)}</div>`:''}</article>`).join('');
  }
  function lawsDrawer(summary){
    const lp=summary.learning_path_v2||{},count=(lp.formula_cards||[]).length;
    return `<div class="s86-law-overlay" id="s86LawOverlay" aria-hidden="true"><section class="s86-law-sheet" role="dialog" aria-modal="true" aria-label="قوانين الدرس"><div class="s86-law-head"><span class="s86-badge-icon">ƒ</span><div><b>قوانين ${esc(summary.title)}</b><span>${count} ${count===1?'بطاقة قانون':'بطاقات قوانين'} — مستقلة عن سرد الملخص</span></div><button type="button" class="s86-law-close" data-action="close-laws" aria-label="إغلاق">×</button></div>${formulasHtml(lp.formula_cards)}</section></div>`;
  }
  function examplesCard(summary){
    const items=summary.learning_path_v2?.worked_examples||[];
    if(!items.length)return '';
    state.exampleIndex=Math.min(Math.max(0,state.exampleIndex),items.length-1);
    const e=items[state.exampleIndex]||items[0];
    return `<section class="s86-full-card"><div class="s86-card-head"><span class="s86-badge-icon">✓</span><div><b>أمثلة محلولة متدرجة</b><span>مثال واحد في كل مرة بدل سرد طويل</span></div></div><div class="s86-example-tabs">${items.map((x,i)=>`<button type="button" class="s86-example-tab ${i===state.exampleIndex?'active':''}" data-example-index="${i}">${esc(x.level||`مثال ${i+1}`)}</button>`).join('')}</div><article class="s86-example"><span class="s86-example-level">${esc(e.level||'مثال')}</span><h4>${esc(e.title)}</h4><p><b>الموقف:</b> ${esc(e.problem)}</p><p><b>لماذا هذه الطريقة؟</b> ${esc(e.why_this_method)}</p><div class="s86-steps">${(e.steps||[]).map(s=>`<div class="s86-step">${esc(s)}</div>`).join('')}</div><p><b>النتيجة:</b> ${esc(e.answer)}</p><p><b>تحقق:</b> ${esc(e.check)}</p></article></section>`;
  }
  function resultHtml(summary){
    const qs=summary.learning_path_v2?.practice_questions||[],answered=Object.keys(state.answers).length;
    if(answered<qs.length)return `<div class="s86-explain">أجب عن الأسئلة الخمسة ليظهر مستوى الإتقان.</div>`;
    const correct=qs.filter((q,i)=>state.answers[i]===q.correct_index).length,score=Math.round(correct/Math.max(1,qs.length)*100),mastered=score>=80;
    return `<section class="s86-result ${mastered?'mastered':'retry'}"><strong>${score}%</strong><b>${mastered?'أتقنت الدرس ✓':'تحتاج مراجعة قصيرة'}</b><p>${mastered?'أصبحت قادرًا على شرح الفكرة واختيار العلاقة المناسبة.':'راجع توضيحات الأسئلة الخاطئة ثم أعد المحاولة.'}</p><div class="s86-practice-nav"><button type="button" class="primary" data-action="reset-practice">إعادة المحاولة</button></div></section>`;
  }
  function practiceCard(summary){
    const qs=summary.learning_path_v2?.practice_questions||[];
    if(!qs.length)return '';
    state.practiceIndex=Math.min(Math.max(0,state.practiceIndex),qs.length-1);
    const qi=state.practiceIndex,q=qs[qi],answer=state.answers[qi];
    return `<section class="s86-full-card" id="s86PracticeCard"><div class="s86-card-head"><span class="s86-badge-icon">?</span><div><b>اختبر فهمك</b><span>سؤال واحد في الشاشة — الإتقان من 4/5</span></div></div><div class="s86-practice-toolbar"><span class="s86-chip">${qi+1} من ${qs.length}</span><div class="s86-practice-dots">${qs.map((_,i)=>`<i class="s86-practice-dot ${i===qi?'active':''} ${state.answers[i]!==undefined?'done':''}"></i>`).join('')}</div></div><article class="s86-question-card"><div class="s86-question-head"><b>${esc(q.source||'تأكد من فهمك')}</b><span>${esc(q.difficulty||'')}</span></div><div class="s86-question-text">${esc(q.question)}</div><div class="s86-options">${(q.options||[]).map((o,oi)=>`<button class="s86-option ${answer!==undefined?(oi===q.correct_index?'correct':oi===answer?'wrong':''):''}" type="button" data-question-index="${qi}" data-option-index="${oi}" ${answer!==undefined?'disabled':''}>${esc(o)}</button>`).join('')}</div>${answer!==undefined?`<div class="s86-explain">${esc(q.explanation||'')}</div>`:''}<div class="s86-practice-nav"><button type="button" data-action="practice-prev" ${qi===0?'disabled':''}>السابق</button><button type="button" class="primary" data-action="practice-next" ${qi===qs.length-1?'disabled':''}>التالي</button></div></article>${resultHtml(summary)}</section>`;
  }
  function renderUnit(stage,unit){
    state.stage=String(stage||'');state.unit=String(unit||'');state.summaryId='';state.reference=null;state.answers={};state.practiceIndex=0;state.exampleIndex=0;
    const p=activate();if(!p)return;
    const items=unitItems(state.stage,state.unit),mastered=items.filter(x=>progress(x).mastered).length,percent=items.length?Math.round(mastered/items.length*100):0;
    p.innerHTML=`<div class="s86-page"><div class="s86-shell">${topbar(state.unit,`${state.stage} • ${items.length} دروس`,false)}<div class="s86-progress" style="--p:${percent}%"><i></i></div><section class="s86-hero"><div class="s86-hero-row"><div><h2>اختر الدرس</h2><p>كل درس مقسم إلى بطاقات مرئية قصيرة، والقوانين في زر مستقل أعلى الصفحة.</p></div><span class="s86-time">${mastered}/${items.length} متقن</span></div></section><div class="s79-lesson-list">${items.map((s,i)=>{const lp=s.learning_path_v2||{},pr=progress(s),idea=s.simple_idea||s.summary||'';return `<button class="s79-lesson-card" type="button" data-summary-id="${esc(s.summary_id||s.id)}"><span class="s79-lesson-num">${i+1}</span><span class="s79-lesson-copy"><b>${esc(s.title)}</b><span>${esc(String(idea).slice(0,105))}</span></span><span class="s79-lesson-meta"><em class="s79-chip ${pr.mastered?'done':''}">${pr.mastered?'متقن ✓':`${lp.estimated_minutes||15} دقيقة`}</em><i class="s79-arrow">‹</i></span></button>`}).join('')}</div></div></div>`;
    bindActions(p);p.scrollTop=0;
  }
  function renderLesson(summary,opts={}){
    const p=activate();if(!p||!summary)return;
    state.summaryId=String(summary.summary_id||summary.id);state.stage=summary.stage;state.unit=summary.unit;
    const lp=summary.learning_path_v2||{},pr=progress(summary),answered=Object.keys(state.answers).length,percent=Math.max(pr.score||0,Math.round(answered/Math.max(1,(lp.practice_questions||[]).length)*100));
    const fromZero=(lp.from_zero||[]).filter(Boolean).map(x=>`<p>${esc(x)}</p>`).join('')+`<div class="s86-chain">${(lp.concept_chain||[]).map((x,i)=>`${i?'<i>←</i>':''}<span>${esc(x)}</span>`).join('')}</div>`;
    const relations=`<div class="s86-mini-grid">${(lp.relationships||[]).map(x=>`<div class="s86-mini"><b>${esc(x.title)}</b><span>${esc(x.explanation)}</span></div>`).join('')}</div>`;
    const definitions=`<div class="s86-mini-grid">${(lp.definitions||[]).map(x=>`<div class="s86-mini"><b>${esc(x.term)}</b><span>${esc(x.meaning)}</span></div>`).join('')}</div>`;
    const compares=`<div class="s86-mini-grid">${(lp.dont_confuse||[]).map(x=>`<div class="s86-mini"><b>${esc(x.title)}</b><span>${esc(x.explanation||x.text||'')}</span></div>`).join('')}</div>`;
    const traps=`${(lp.common_traps||[]).map(x=>`<div class="s86-trap">${esc(x)}</div>`).join('')}`;
    const patterns=`<div class="s86-mini-grid">${(lp.exam_patterns||[]).map(x=>`<div class="s86-mini"><b>${esc(x.title||x.type||'نمط سؤال')}</b><span>${esc(x.description||x.how_it_appears||x.tip||'')}</span></div>`).join('')}</div>`;
    const t=lp.takeaway||{};
    const takeaway=`<section class="s86-full-card"><div class="s86-card-head"><span class="s86-badge-icon">★</span><div><b>خلاصة الدرس</b><span>أربع نقاط تحفظها قبل الخروج</span></div></div><div class="s86-takeaway-grid"><div><b>الفكرة الأهم</b>${esc(t.main_idea||'')}</div><div><b>القانون أو القاعدة</b>${esc(t.main_rule||'')}</div><div><b>الفخ الأهم</b>${esc(t.main_trap||'')}</div><div><b>علامة الفهم</b>${esc(t.understanding_signal||'')}</div></div></section>`;
    const before=`<section class="s86-before"><div class="s86-before-head"><span class="s86-badge-icon">◉</span><div><b>قبل أن تبدأ</b><span>تأكد من الأساسيات ثم أجب عن التشخيص</span></div></div><div class="s86-prereq-row">${(lp.prerequisites||[]).map(x=>`<div class="s86-prereq"><b>${esc(x.title)}</b><span>${esc(x.reason)}</span></div>`).join('')}</div>${diagnosticHtml(lp.diagnostic_question)}</section>`;
    const prevNext=`<div class="s86-prev-next">${lp.navigation?.previous_summary_id?`<button type="button" data-action="prev-lesson" data-summary-id="${esc(lp.navigation.previous_summary_id)}">الدرس السابق</button>`:'<span></span>'}${lp.navigation?.next_summary_id?`<button type="button" class="primary" data-action="next-lesson" data-summary-id="${esc(lp.navigation.next_summary_id)}">الدرس التالي</button>`:'<span></span>'}</div>`;
    p.innerHTML=`<div class="s86-page"><div class="s86-shell">${topbar(summary.title,`${summary.stage} • ${summary.unit}`,true)}<div class="s86-progress" style="--p:${percent}%"><i></i></div>${referenceBox(summary)}<section class="s86-hero"><div class="s86-hero-row"><div><h2>${esc(summary.title)}</h2><p>${esc(summary.simple_idea||'')}</p></div><span class="s86-time">${lp.estimated_minutes||15} دقيقة</span></div></section>${before}<div class="s86-summary-grid">${tile('zero','الفكرة من الصفر',lp.from_zero,fromZero)}${tile('map','خريطة الفهم',lp.relationships,relations)}${tile('definitions','التعريفات الأساسية',lp.definitions,definitions)}${tile('compare','لا تخلط',lp.dont_confuse,compares)}${tile('traps','الفخاخ الشائعة',lp.common_traps,traps)}${tile('patterns','كيف يأتي في التحصيلي؟',lp.exam_patterns,patterns)}</div>${examplesCard(summary)}${practiceCard(summary)}${takeaway}${prevNext}${lawsDrawer(summary)}</div></div>`;
    bindActions(p);
    if(opts.preserveScroll!==undefined)p.scrollTop=opts.preserveScroll;else p.scrollTop=0;
    if(state.reference)setTimeout(()=>p.querySelector('.s86-reference-focus')?.scrollIntoView({behavior:'smooth',block:'center'}),110);
  }
  function openLesson(id,reference=null){
    const summary=byId(id);if(!summary||!summary.learning_path_v2)return;
    state.answers={};state.reference=reference;state.practiceIndex=0;state.exampleIndex=0;renderLesson(summary);
  }
  function openReference(r){
    if(!r)return;
    const sid=r.summary_id||r.summary?.summary_id||r.summary?.id,bid=r.block_id||r.block?.id,summary=byId(sid);if(!summary)return;
    openLesson(sid,{summary_id:sid,block_id:bid});
  }
  function answerDiagnostic(index){state.diagnostic[state.summaryId]=index;const p=page(),y=p?.scrollTop||0;renderLesson(byId(state.summaryId),{preserveScroll:y});}
  function answerQuestion(qi,oi){
    if(state.answers[qi]!==undefined)return;
    state.answers[qi]=oi;
    const summary=byId(state.summaryId),qs=summary?.learning_path_v2?.practice_questions||[];
    if(Object.keys(state.answers).length===qs.length){const correct=qs.filter((q,i)=>state.answers[i]===q.correct_index).length,score=Math.round(correct/Math.max(1,qs.length)*100);safeSet(summary.learning_path_v2.mastery.status_storage_key,{answered:qs.length,correct,score,mastered:score>=80,updated_at:new Date().toISOString()});}
    const p=page(),y=p?.scrollTop||0;renderLesson(summary,{preserveScroll:y});
  }
  function resetPractice(){state.answers={};state.practiceIndex=0;const s=byId(state.summaryId);if(s)safeSet(s.learning_path_v2.mastery.status_storage_key,{answered:0,correct:0,score:0,mastered:false});renderLesson(s);setTimeout(()=>page()?.querySelector('#s86PracticeCard')?.scrollIntoView({behavior:'smooth',block:'start'}),60);}
  function openLaws(){const o=document.getElementById('s86LawOverlay');if(!o)return;o.classList.add('open');o.setAttribute('aria-hidden','false');document.body.classList.add('s86-laws-open');}
  function closeLaws(){const o=document.getElementById('s86LawOverlay');if(!o)return;o.classList.remove('open');o.setAttribute('aria-hidden','true');document.body.classList.remove('s86-laws-open');}
  function bindActions(root){
    root.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',e=>{
      const action=el.dataset.action;
      if(action==='back-unit'){if(state.summaryId)renderUnit(state.stage,state.unit);else window.s71OpenStage?.(state.stage);}
      else if(action==='open-laws')openLaws();
      else if(action==='close-laws')closeLaws();
      else if(action==='reset-practice')resetPractice();
      else if(action==='prev-lesson'||action==='next-lesson')openLesson(el.dataset.summaryId);
      else if(action==='practice-prev'){state.practiceIndex=Math.max(0,state.practiceIndex-1);const p=page(),y=p?.scrollTop||0;renderLesson(byId(state.summaryId),{preserveScroll:y});}
      else if(action==='practice-next'){state.practiceIndex=Math.min((byId(state.summaryId)?.learning_path_v2?.practice_questions||[]).length-1,state.practiceIndex+1);const p=page(),y=p?.scrollTop||0;renderLesson(byId(state.summaryId),{preserveScroll:y});}
      e.stopPropagation();
    }));
    root.querySelectorAll('[data-summary-id].s79-lesson-card').forEach(el=>el.addEventListener('click',()=>openLesson(el.dataset.summaryId)));
    root.querySelectorAll('[data-diagnostic-option]').forEach(el=>el.addEventListener('click',()=>answerDiagnostic(Number(el.dataset.diagnosticOption))));
    root.querySelectorAll('[data-question-index][data-option-index]').forEach(el=>el.addEventListener('click',()=>answerQuestion(Number(el.dataset.questionIndex),Number(el.dataset.optionIndex))));
    root.querySelectorAll('[data-example-index]').forEach(el=>el.addEventListener('click',()=>{state.exampleIndex=Number(el.dataset.exampleIndex)||0;const p=page(),y=p?.scrollTop||0;renderLesson(byId(state.summaryId),{preserveScroll:y});}));
    const overlay=root.querySelector('#s86LawOverlay');if(overlay)overlay.addEventListener('click',e=>{if(e.target===overlay)closeLaws();});
  }
  function install(){
    const oldUnit=window.s71OpenUnit;
    window.s86OpenUnit=renderUnit;window.s86OpenLesson=openLesson;window.s86OpenReference=openReference;
    window.s79OpenUnit=renderUnit;window.s79OpenLesson=openLesson;window.s79OpenReference=openReference;
    window.s71OpenUnit=function(stage,unit){const items=unitItems(stage,unit);if(items.length)return renderUnit(stage,unit);return typeof oldUnit==='function'?oldUnit(stage,unit):undefined};
    window.SuhailPhysics86={version:VERSION,renderUnit,openLesson,openReference,progress,state,openLaws,closeLaws};
    if(window.SuhailPhysics79)Object.assign(window.SuhailPhysics79,{version:VERSION,renderUnit,openLesson,openReference,state});
    window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
