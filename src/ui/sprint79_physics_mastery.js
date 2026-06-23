/* Sprint 79 — final physics mastery experience. */
(function(){
  'use strict';
  const VERSION='79.0.0';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const bank=()=>{try{return Array.isArray(window.smartSummaries)?window.smartSummaries:(typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries:[])}catch(_){return[]}};
  const page=()=>document.getElementById('summariesPage');
  const byId=id=>bank().find(s=>String(s.summary_id||s.id)===String(id))||null;
  const physics=()=>bank().filter(s=>String(s.subject||'')==='فيزياء'&&s.learning_path_v2);
  const state={stage:'',unit:'',summaryId:'',answers:{},diagnostic:{},reference:null};
  const safeGet=(key,fallback=null)=>{try{const v=localStorage.getItem(key);return v?JSON.parse(v):fallback}catch(_){return fallback}};
  const safeSet=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch(_){return false}};
  const iconMap={before:'◉',zero:'✦',map:'↔',definitions:'أ',formulas:'ƒ',examples:'✓',compare:'⇄',traps:'!',patterns:'▦',practice:'?',takeaway:'★'};
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
  function topbar(title,subtitle,backAction){return `<div class="s79-topbar"><button class="s79-back" type="button" data-action="${esc(backAction)}" aria-label="رجوع">›</button><div class="s79-heading"><b>${esc(title)}</b><span>${esc(subtitle)}</span></div></div>`}
  function bindActions(root){
    root.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',()=>{
      const action=el.dataset.action;
      if(action==='back-stage')window.s71OpenStage?.(state.stage);
      else if(action==='back-unit')renderUnit(state.stage,state.unit);
      else if(action==='reset-practice')resetPractice();
      else if(action==='prev-lesson'||action==='next-lesson')openLesson(el.dataset.summaryId);
    }));
    root.querySelectorAll('[data-summary-id].s79-lesson-card').forEach(el=>el.addEventListener('click',()=>openLesson(el.dataset.summaryId)));
    root.querySelectorAll('[data-diagnostic-option]').forEach(el=>el.addEventListener('click',()=>answerDiagnostic(Number(el.dataset.diagnosticOption))));
    root.querySelectorAll('[data-question-index][data-option-index]').forEach(el=>el.addEventListener('click',()=>answerQuestion(Number(el.dataset.questionIndex),Number(el.dataset.optionIndex))));
  }
  function renderUnit(stage,unit){
    state.stage=String(stage||'');state.unit=String(unit||'');state.summaryId='';state.reference=null;state.answers={};
    const p=activate();if(!p)return;
    const items=unitItems(state.stage,state.unit);
    const mastered=items.filter(x=>progress(x).mastered).length;
    const percent=items.length?Math.round(mastered/items.length*100):0;
    p.innerHTML=`<div class="s79-page"><div class="s79-shell">${topbar(state.unit,`${state.stage} • ${items.length} دروس`,'back-stage')}<div class="s79-progress" style="--p:${percent}%"><i></i></div><section class="s79-unit-intro"><b>ابدأ بالدرس المناسب لك</b><p>كل درس يبدأ بتشخيص سريع، ثم يشرح الفكرة من الصفر ويعطيك أمثلة متدرجة و5 أسئلة إتقان. يعتبر الدرس متقنًا عند الإجابة عن 4 من 5 بشكل صحيح.</p></section><div class="s79-lesson-list">${items.map((s,i)=>{
      const lp=s.learning_path_v2||{},pr=progress(s),idea=s.simple_idea||s.summary||'';
      return `<button class="s79-lesson-card" type="button" data-summary-id="${esc(s.summary_id||s.id)}"><span class="s79-lesson-num">${i+1}</span><span class="s79-lesson-copy"><b>${esc(s.title)}</b><span>${esc(String(idea).slice(0,115))}</span></span><span class="s79-lesson-meta"><em class="s79-chip ${pr.mastered?'done':''}">${pr.mastered?'متقن ✓':`${lp.estimated_minutes||15} دقيقة`}</em><i class="s79-arrow">‹</i></span></button>`}).join('')}</div></div></div>`;
    bindActions(p);p.scrollTop=0;
  }
  function section(id,title,body,open=false){return `<details class="s79-section" data-section="${esc(id)}" ${open?'open':''}><summary><span class="s79-section-icon">${iconMap[id]||'•'}</span>${esc(title)}</summary><div class="s79-section-body">${body}</div></details>`}
  function referenceBox(summary){
    const r=state.reference;if(!r||String(r.summary_id)!==String(summary.summary_id||summary.id))return '';
    const block=(summary.knowledge_blocks||[]).find(b=>String(b.id)===String(r.block_id));
    if(!block)return '';
    return `<section class="s79-reference-focus flash" data-block-id="${esc(block.id)}"><small>وصلت من سؤال مرتبط</small><b>${esc(block.title||summary.title)}</b><span>${esc(block.content||'')}</span></section>`;
  }
  function diagnosticHtml(q){
    if(!q)return '<p>ابدأ بقراءة الفكرة من الصفر.</p>';
    const answered=state.diagnostic[state.summaryId];
    return `<div class="s79-diagnostic"><div class="s79-question-text">${esc(q.question)}</div><div class="s79-options">${(q.options||[]).map((o,i)=>`<button class="s79-option ${answered!==undefined?(i===q.correct_index?'correct':i===answered?'wrong':''):''}" type="button" data-diagnostic-option="${i}" ${answered!==undefined?'disabled':''}>${esc(o)}</button>`).join('')}</div>${answered!==undefined?`<div class="s79-explain">${esc(q.explanation||'')}</div>`:''}</div>`;
  }
  function formulasHtml(cards){return (cards||[]).map(f=>`<article class="s79-formula"><div class="s79-formula-head"><b>${esc(f.title)}</b><span class="s79-chip">${String(f.formula||'').includes('=')?'قانون':'قاعدة'}</span></div><div class="s79-formula-code">${esc(f.formula)}</div><div class="s79-formula-use"><b>متى أستخدمه؟</b> ${esc(f.when_to_use||f.meaning||'')}</div>${(f.symbols||[]).length?`<div class="s79-symbols">${f.symbols.map(s=>`<span><code>${esc(s.symbol)}</code> = ${esc(s.meaning)} (${esc(s.unit)})</span>`).join('')}</div>`:''}<div class="s79-formula-warning"><b>متى لا أستخدمه؟</b> ${esc(f.when_not_to_use||'')}</div>${f.common_error?`<div class="s79-formula-warning"><b>الخطأ الشائع:</b> ${esc(f.common_error)}</div>`:''}</article>`).join('')}
  function examplesHtml(items){return (items||[]).map(e=>`<article class="s79-example"><span class="s79-example-level">${esc(e.level)}</span><h4>${esc(e.title)}</h4><p><b>الموقف:</b> ${esc(e.problem)}</p><p><b>لماذا هذه الطريقة؟</b> ${esc(e.why_this_method)}</p><div class="s79-steps">${(e.steps||[]).map(s=>`<div class="s79-step">${esc(s)}</div>`).join('')}</div><p><b>النتيجة:</b> ${esc(e.answer)}</p><p><b>تحقق:</b> ${esc(e.check)}</p></article>`).join('')}
  function questionsHtml(summary){
    const qs=summary.learning_path_v2?.practice_questions||[];
    return `${qs.map((q,qi)=>{
      const answer=state.answers[qi];
      return `<article class="s79-question"><div class="s79-question-head"><span class="s79-question-index">${qi+1} من ${qs.length}</span><b>${esc(q.source||'اختبر فهمك')}</b><span class="s79-difficulty">${esc(q.difficulty||'')}</span></div><div class="s79-question-text">${esc(q.question)}</div><div class="s79-options">${(q.options||[]).map((o,oi)=>`<button class="s79-option ${answer!==undefined?(oi===q.correct_index?'correct':oi===answer?'wrong':''):''}" type="button" data-question-index="${qi}" data-option-index="${oi}" ${answer!==undefined?'disabled':''}>${esc(o)}</button>`).join('')}</div>${answer!==undefined?`<div class="s79-explain">${esc(q.explanation||'')}</div>`:''}</article>`}).join('')}${resultHtml(summary)}`;
  }
  function resultHtml(summary){
    const qs=summary.learning_path_v2?.practice_questions||[],answered=Object.keys(state.answers).length;
    if(answered<qs.length)return `<div class="s79-note">أجب عن الأسئلة الخمسة ليظهر مستوى الإتقان.</div>`;
    const correct=qs.filter((q,i)=>state.answers[i]===q.correct_index).length,score=Math.round(correct/qs.length*100),mastered=score>=80;
    return `<section class="s79-result ${mastered?'mastered':'retry'}"><strong>${score}%</strong><b>${mastered?'أتقنت الدرس ✓':'تحتاج مراجعة قصيرة'}</b><p>${mastered?'أصبحت قادرًا على شرح الفكرة واختيار العلاقة المناسبة.':'راجع التوضيحات في الأسئلة الخاطئة ثم أعد المحاولة؛ لا يلزم إعادة قراءة كل الدرس.'}</p><div class="s79-actions"><button class="s79-primary" type="button" data-action="reset-practice">إعادة المحاولة</button></div></section>`;
  }
  function renderLesson(summary){
    const p=activate();if(!p||!summary)return;
    state.summaryId=String(summary.summary_id||summary.id);state.stage=summary.stage;state.unit=summary.unit;
    const lp=summary.learning_path_v2||{},pr=progress(summary),answered=Object.keys(state.answers).length,percent=Math.max(pr.score||0,Math.round(answered/Math.max(1,(lp.practice_questions||[]).length)*100));
    const before=`${diagnosticHtml(lp.diagnostic_question)}<div class="s79-grid">${(lp.prerequisites||[]).map(x=>`<div class="s79-note"><b>${esc(x.title)}</b>${esc(x.reason)}</div>`).join('')}</div>`;
    const fromZero=(lp.from_zero||[]).filter(Boolean).map(x=>`<p>${esc(x)}</p>`).join('')+`<div class="s79-chain">${(lp.concept_chain||[]).map((x,i)=>`${i?'<i>←</i>':''}<span>${esc(x)}</span>`).join('')}</div>`;
    const relations=`<div class="s79-grid">${(lp.relationships||[]).map(x=>`<div class="s79-relation"><b>${esc(x.title)}</b><span>${esc(x.explanation)}</span></div>`).join('')}</div>`;
    const definitions=`<div class="s79-grid">${(lp.definitions||[]).map(x=>`<div class="s79-definition"><b>${esc(x.term)}</b><span>${esc(x.meaning)}</span></div>`).join('')}</div>`;
    const compares=`<div class="s79-grid">${(lp.dont_confuse||[]).map(x=>`<div class="s79-compare"><b>${esc(x.title)}</b><span>${esc(x.explanation||x.text||'')}</span></div>`).join('')}</div>`;
    const traps=`<div class="s79-grid">${(lp.common_traps||[]).map(x=>`<div class="s79-trap">${esc(x)}</div>`).join('')}</div>`;
    const patterns=`<div class="s79-grid">${(lp.exam_patterns||[]).map(x=>`<div class="s79-pattern"><b>${esc(x.title||x.type||'نمط سؤال')}</b><span>${esc(x.description||x.how_it_appears||x.tip||'')}</span></div>`).join('')}</div>`;
    const t=lp.takeaway||{};const takeaway=`<div class="s79-takeaway"><div><b>الفكرة الأهم</b>${esc(t.main_idea||'')}</div><div><b>القانون أو القاعدة الأهم</b>${esc(t.main_rule||'')}</div><div><b>الفخ الأهم</b>${esc(t.main_trap||'')}</div><div><b>كيف تعرف أنك فهمت؟</b>${esc(t.understanding_signal||'')}</div></div>`;
    p.innerHTML=`<div class="s79-page"><div class="s79-shell">${topbar(summary.title,`${summary.stage} • ${summary.unit}`,'back-unit')}<div class="s79-progress" style="--p:${percent}%"><i></i></div>${referenceBox(summary)}<section class="s79-hero"><div class="s79-hero-row"><div><h2>${esc(summary.title)}</h2><p>${esc(summary.simple_idea||'')}</p></div><span class="s79-time">${lp.estimated_minutes||15} دقيقة</span></div></section>${section('before','قبل أن تبدأ',before,true)}${section('zero','الفكرة من الصفر',fromZero,true)}${section('map','خريطة الفهم والربط',relations)}${section('definitions','التعريفات الأساسية',definitions)}${section('formulas','القوانين بمعناها',formulasHtml(lp.formula_cards))}${section('examples','أمثلة محلولة متدرجة',examplesHtml(lp.worked_examples))}${section('compare','لا تخلط',compares)}${section('traps','الفخاخ الشائعة',traps)}${section('patterns','كيف يظهر في التحصيلي؟',patterns)}${section('practice','اختبر فهمك — 5 أسئلة',questionsHtml(summary),true)}${section('takeaway','خلاصة الدرس',takeaway,true)}<div class="s79-prev-next">${lp.navigation?.previous_summary_id?`<button class="s79-secondary" data-action="prev-lesson" data-summary-id="${esc(lp.navigation.previous_summary_id)}">الدرس السابق</button>`:'<span></span>'}${lp.navigation?.next_summary_id?`<button class="s79-primary" data-action="next-lesson" data-summary-id="${esc(lp.navigation.next_summary_id)}">الدرس التالي</button>`:'<span></span>'}</div></div></div>`;
    bindActions(p);p.scrollTop=0;
    if(state.reference)setTimeout(()=>p.querySelector('.s79-reference-focus')?.scrollIntoView({behavior:'smooth',block:'center'}),120);
  }
  function openLesson(id,reference=null){
    const summary=byId(id);if(!summary||!summary.learning_path_v2)return;
    state.answers={};state.reference=reference;renderLesson(summary);
  }
  function answerDiagnostic(index){state.diagnostic[state.summaryId]=index;renderLesson(byId(state.summaryId));}
  function answerQuestion(qi,oi){
    if(state.answers[qi]!==undefined)return;
    state.answers[qi]=oi;
    const summary=byId(state.summaryId),qs=summary?.learning_path_v2?.practice_questions||[];
    if(Object.keys(state.answers).length===qs.length){
      const correct=qs.filter((q,i)=>state.answers[i]===q.correct_index).length,score=Math.round(correct/qs.length*100);
      safeSet(summary.learning_path_v2.mastery.status_storage_key,{answered:qs.length,correct,score,mastered:score>=80,updated_at:new Date().toISOString()});
    }
    renderLesson(summary);
    setTimeout(()=>page()?.querySelector(`[data-question-index="${qi}"]`)?.closest('.s79-question')?.scrollIntoView({behavior:'smooth',block:'center'}),60);
  }
  function resetPractice(){state.answers={};const s=byId(state.summaryId);if(s)safeSet(s.learning_path_v2.mastery.status_storage_key,{answered:0,correct:0,score:0,mastered:false});renderLesson(s);}
  function openReference(r){
    if(!r)return;
    const sid=r.summary_id||r.summary?.summary_id||r.summary?.id;
    const bid=r.block_id||r.block?.id;
    const summary=byId(sid);if(!summary)return;
    openLesson(sid,{summary_id:sid,block_id:bid});
  }
  function install(){
    const oldUnit=window.s71OpenUnit;
    window.s79OpenUnit=renderUnit;window.s79OpenLesson=openLesson;window.s79OpenReference=openReference;
    window.s71OpenUnit=function(stage,unit){const items=unitItems(stage,unit);if(items.length)return renderUnit(stage,unit);return typeof oldUnit==='function'?oldUnit(stage,unit):undefined};
    window.SuhailPhysics79={version:VERSION,renderUnit,openLesson,openReference,progress,state};
    window.SUHAIL_RELEASE=VERSION;
    document.documentElement.dataset.suhailRelease=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
