/* Sprint 72 — exact summary deep links and difficulty-aware explanations. */
(function(){
  'use strict';
  const VERSION='72.0.0';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const labelKey=v=>String(v??'').trim().replace(/^ال/,'').replace(/[\sـ]/g,'');
  const bank=()=>{try{return Array.isArray(window.smartSummaries)?window.smartSummaries:(typeof smartSummaries!=='undefined'?smartSummaries:[])}catch(_){return[]}};
  const qbank=()=>{try{return Array.isArray(window.questions)?window.questions:(typeof questions!=='undefined'?questions:[])}catch(_){return[]}};
  const findSummary=id=>bank().find(s=>String(s.summary_id||s.id)===String(id))||null;
  function findBlock(id){for(const s of bank()){const b=(s.knowledge_blocks||[]).find(x=>String(x.id)===String(id));if(b)return {summary:s,block:b};}return null;}
  function ref(q){
    if(!q||!q.summary_id||!q.summary_block_id)return null;
    const found=findBlock(q.summary_block_id), s=findSummary(q.summary_id);
    if(!found||!s||String(found.summary.summary_id||found.summary.id)!==String(s.summary_id||s.id))return null;
    return {question:q,summary:s,block:found.block,exam:q.summary_exam||'تحصيلي',subject:q.summary_subject||s.subject,stage:q.summary_stage||s.stage,unit:q.summary_unit||s.unit,lesson:q.summary_lesson||q.summary_title||s.title};
  }
  function currentQ(){try{return activeQuestions?.[activeIndex]||null}catch(_){return null}}
  function ensureModal(){
    let m=document.getElementById('s72LinkModal');if(m)return m;
    m=document.createElement('div');m.id='s72LinkModal';m.className='s72-link-modal';
    m.innerHTML='<div class="s72-link-sheet" role="dialog" aria-modal="true"><div class="s72-link-head"><span>المرجع المرتبط بالسؤال</span><button type="button" aria-label="إغلاق">×</button></div><div class="s72-link-path" id="s72LinkPath"></div><div class="s72-link-title" id="s72LinkTitle"></div><div class="s72-link-text" id="s72LinkText"></div><div class="s72-link-actions"><button class="primary" id="s72OpenFull">فتح مكانه في الملخص</button><button class="secondary" id="s72Close">إغلاق</button></div></div>';
    m.addEventListener('click',e=>{if(e.target===m)closeModal()});
    m.querySelector('.s72-link-head button').onclick=closeModal;m.querySelector('#s72Close').onclick=closeModal;
    document.body.appendChild(m);return m;
  }
  function closeModal(){document.getElementById('s72LinkModal')?.classList.remove('open')}
  let pending=null;
  function openPreview(q){
    const r=ref(q);if(!r)return;
    const m=ensureModal();
    m.querySelector('#s72LinkPath').textContent=[r.stage,r.unit,r.lesson].filter(Boolean).join(' • ');
    m.querySelector('#s72LinkTitle').textContent=r.block.title||r.lesson;
    m.querySelector('#s72LinkText').textContent=r.block.content||'';
    m.querySelector('#s72OpenFull').onclick=()=>{closeModal();openFull(q)};
    m.classList.add('open');
  }
  function addFocus(){
    if(!pending)return false;
    const page=document.querySelector('#summariesPage .s17-unit-summary');
    const body=page?.querySelector('.s14-body');if(!body)return false;
    page.querySelectorAll('.s72-summary-focus').forEach(x=>x.remove());
    const r=pending;
    const box=document.createElement('section');box.className='s72-summary-focus';box.dataset.blockId=r.block.id;
    box.innerHTML='<div class="s72-focus-kicker">وصلت من سؤال مرتبط</div><div class="s72-focus-title">'+esc(r.lesson)+'</div><div class="s72-focus-block"><b>'+esc(r.block.title)+'</b><span>'+esc(r.block.content)+'</span></div>';
    const titleRow=body.querySelector('.s14-title-row');
    if(titleRow)titleRow.insertAdjacentElement('afterend',box);else body.prepend(box);
    page.querySelectorAll('.s17-lesson-pill').forEach(p=>{if(String(p.textContent||'').trim()===String(r.lesson||'').trim())p.classList.add('s72-linked-lesson')});
    setTimeout(()=>box.scrollIntoView({behavior:'smooth',block:'center'}),80);
    pending=null;return true;
  }
  function openFull(q){
    const r=ref(q);if(!r)return;
    pending=r;
    try{
      if(typeof window.s71OpenUnit==='function')window.s71OpenUnit(r.stage,r.unit);
      else if(typeof window.s17OpenUnitStable==='function')window.s17OpenUnitStable(encodeURIComponent(r.stage),encodeURIComponent(r.unit));
      else if(typeof window.openSummaryUnit==='function')window.openSummaryUnit(r.subject,r.unit,r.exam);
    }catch(_){return;}
    let tries=0;const timer=setInterval(()=>{tries++;if(addFocus()||tries>30)clearInterval(timer)},60);
  }
  function decorateCurrent(){
    const box=document.getElementById('questionSummaryLink'),q=currentQ();if(!box)return;
    const r=ref(q);
    if(!r){box.innerHTML='';box.classList.add('hidden');box.onclick=null;box.removeAttribute('data-s72');return;}
    const sig=String(q.id||q.public_id)+'::'+r.block.id;
    if(box.dataset.s72===sig)return;
    box.dataset.s72=sig;box.dataset.s69Signature=sig;
    const sameTitle=labelKey(r.block.title)===labelKey(r.lesson);
    const detail=sameTitle?String(r.block.content||'').slice(0,105):(String(r.block.title||'')+' — '+String(r.block.content||'').slice(0,90));
    box.innerHTML='<button type="button" class="s69-knowledge-link s72-question-link"><span class="s72-link-icon">↗</span><span><b>'+esc(r.lesson)+'</b><small>'+esc(detail)+'</small></span><em>‹</em></button>';
    box.classList.remove('hidden');box.onclick=()=>openPreview(q);
  }
  function decorateResults(){
    document.querySelectorAll('.result-question-card').forEach((card,idx)=>{
      const q=(window.activeQuestions||[])[idx];if(!q)return;
      const r=ref(q),mode=String(q.explanation_mode||'none'),difficulty=String(q.difficulty||'');
      const qid=String(q.id||q.public_id||idx),blockId=r?String(r.block.id):'none';
      const signature=[qid,mode,difficulty,blockId].join('::');
      card.querySelectorAll('.summary-ref-pill,.no-summary-link,.s68-result-explain').forEach(x=>x.remove());
      if(card.dataset.s72Result===signature)return;
      card.querySelectorAll('.s72-result-link,.s72-result-explain').forEach(x=>x.remove());
      if(mode!=='none'&&(difficulty==='متوسط'||difficulty==='صعب')){
        const text=String(q.explanation?.summary||q.explain||'').trim();
        if(text){const ex=document.createElement('div');ex.className='s72-result-explain';ex.textContent=text;card.appendChild(ex);}
      }
      if(r){
        const b=document.createElement('button');b.type='button';b.className='s72-result-link';
        const sameTitle=labelKey(r.block.title)===labelKey(r.lesson);
        const detail=sameTitle?String(r.block.content||'').slice(0,85):String(r.block.title||'');
        b.innerHTML='<span><b>'+esc(r.lesson)+'</b><small>'+esc(detail)+'</small></span><em>فتح الملخص ‹</em>';
        b.onclick=()=>openPreview(q);card.appendChild(b);
      }
      card.dataset.s72Result=signature;
    });
  }
  function patch(name,after){const old=window[name];if(typeof old!=='function'||old.__s72)return;const fn=function(){const out=old.apply(this,arguments);setTimeout(after,70);return out};Object.assign(fn,old);fn.__s72=true;window[name]=fn;}
  function install(){
    window.getQuestionSummaryRef=function(q){const r=ref(q);return r?{exam:r.exam,subject:r.subject,stage:r.stage,unit:r.unit,lesson:r.lesson,summary_id:r.summary.summary_id||r.summary.id,block_id:r.block.id}:null};
    patch('loadCurrentQuestion',decorateCurrent);patch('finishExam',decorateResults);patch('prevQuiz',decorateCurrent);patch('nextQuiz',decorateCurrent);
    ensureModal();setTimeout(decorateCurrent,180);
    let t=null;new MutationObserver(()=>{clearTimeout(t);t=setTimeout(()=>{decorateCurrent();if(document.getElementById('examSummary')?.classList.contains('hidden')===false)decorateResults();if(pending)addFocus()},45)}).observe(document.body,{childList:true,subtree:true});
    window.SuhailLink72={version:VERSION,ref,openPreview,openFull,findBlock};window.SUHAIL_RELEASE=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
