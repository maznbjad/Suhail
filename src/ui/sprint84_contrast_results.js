/* Sprint 84 — global exam contrast audit and direct result-to-summary navigation. */
(function(){
  'use strict';
  const VERSION='84.0.0';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

  function activeList(){
    try{return Array.isArray(activeQuestions)?activeQuestions:[];}catch(_){return Array.isArray(window.activeQuestions)?window.activeQuestions:[];}
  }
  function resultList(){
    try{return Array.isArray(questionResults)?questionResults:[];}catch(_){return Array.isArray(window.questionResults)?window.questionResults:[];}
  }
  function bridgeGlobals(){
    /* Sprint 72 used window.activeQuestions, while the main app declares it with let. */
    try{window.activeQuestions=activeList();}catch(_){}
    try{window.questionResults=resultList();}catch(_){}
  }
  function exactRef(q){
    if(!q)return null;
    try{
      const r=window.SuhailLink72?.ref?.(q);
      if(r)return r;
    }catch(_){}
    if(!q.summary_id||!q.summary_block_id)return null;
    return {
      question:q,
      exam:q.summary_exam||'تحصيلي',
      subject:q.summary_subject||q.subject||'',
      stage:q.summary_stage||'',
      unit:q.summary_unit||q.unit||'',
      lesson:q.summary_lesson||q.summary_title||'',
      summary:{summary_id:q.summary_id,id:q.summary_id},
      block:{id:q.summary_block_id,title:q.summary_block_title||q.summary_lesson||'',content:q.summary_block_content||''}
    };
  }
  function openExact(q,r){
    if(!q||!r)return;
    try{
      if(window.SuhailLink72?.openFull){window.SuhailLink72.openFull(q);return;}
      if(window.s79OpenReference){
        window.s79OpenReference({
          summary_id:r.summary?.summary_id||r.summary?.id||q.summary_id,
          block_id:r.block?.id||q.summary_block_id,
          stage:r.stage||q.summary_stage,
          unit:r.unit||q.summary_unit,
          lesson:r.lesson||q.summary_lesson
        });
        return;
      }
      if(window.openSummaryUnit){window.openSummaryUnit(r.subject,r.unit,r.exam);}
    }catch(err){
      console.error('Suhail Sprint 84 summary navigation failed',err);
    }
  }
  function markAnswerState(card,idx){
    const rr=resultList()[idx]||{};
    const answered=rr.answered===true||Number.isInteger(rr.selectedIndex);
    const lines=[...card.querySelectorAll('.result-answer-line,.s68-result-choice')];
    const answerLine=lines.find(x=>String(x.textContent||'').includes('لم تتم الإجابة'))||lines.find(x=>String(x.textContent||'').includes('إجابتك'))||lines[0];
    const badge=card.querySelector('.result-badge');
    card.classList.toggle('s84-unanswered-card',!answered);
    lines.forEach(x=>x.classList.remove('s84-unanswered-line'));
    if(answerLine)answerLine.classList.toggle('s84-unanswered-line',!answered);
    if(badge&&!answered){
      badge.textContent='لم يُجب';
      badge.classList.remove('ok','no');
      badge.classList.add('skipped');
    }
  }
  function addDirectLink(card,q){
    card.querySelectorAll('.s72-result-link,.s84-result-summary-btn').forEach(x=>x.remove());
    const r=exactRef(q);
    if(!r)return;
    card.querySelectorAll('.summary-ref-pill,.no-summary-link').forEach(x=>x.remove());
    const btn=document.createElement('button');
    btn.type='button';
    btn.className='s84-result-summary-btn';
    const lesson=r.lesson||r.block?.title||r.unit||'الملخص المرتبط';
    const path=[r.stage,r.unit].filter(Boolean).join(' • ');
    btn.innerHTML='<span class="s84-result-summary-copy"><b>'+esc(lesson)+'</b><small>'+esc(path||'فتح الموضع المرتبط بالسؤال')+'</small></span><span class="s84-result-summary-action">فتح الملخص ‹</span>';
    const handler=function(e){
      e.preventDefault();e.stopPropagation();
      if(typeof e.stopImmediatePropagation==='function')e.stopImmediatePropagation();
      openExact(q,r);
    };
    btn.addEventListener('click',handler,{capture:true});
    card.appendChild(btn);
  }
  function stabilizeResults(){
    bridgeGlobals();
    const qs=activeList();
    document.querySelectorAll('#exercisePage .result-question-card').forEach((card,idx)=>{
      markAnswerState(card,idx);
      addDirectLink(card,qs[idx]);
    });
  }
  function stabilizeCardText(){
    /* Remove legacy inline visibility/opacity only from semantic text roles. */
    document.querySelectorAll('.source-option-title,.source-option-sub,.main-section-title,.main-section-sub,.result-answer-line').forEach(el=>{
      el.style.removeProperty('color');
      el.style.removeProperty('opacity');
      el.style.removeProperty('visibility');
    });
  }
  function afterExam(){
    [0,90,180,320].forEach(ms=>setTimeout(()=>{stabilizeCardText();stabilizeResults();},ms));
  }
  function patch(name,after){
    const old=window[name];
    if(typeof old!=='function'||old.__s84)return;
    const fn=function(){bridgeGlobals();const out=old.apply(this,arguments);after();return out;};
    Object.assign(fn,old);fn.__s84=true;window[name]=fn;
  }
  function install(){
    bridgeGlobals();
    patch('finishExam',afterExam);
    patch('loadCurrentQuestion',()=>setTimeout(bridgeGlobals,0));
    patch('beginExamWithMode',()=>setTimeout(()=>{bridgeGlobals();stabilizeCardText();},0));
    stabilizeCardText();
    if(!document.getElementById('examSummary')?.classList.contains('hidden'))afterExam();
    window.SuhailContrast84={version:VERSION,stabilizeCardText,stabilizeResults,openExact,exactRef};
    window.SUHAIL_RELEASE=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
