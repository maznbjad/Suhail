/* Unified Qudurat bank + question presentation (updated in Sprint 62). */
(function(){
  'use strict';
  const VERSION='62.0.0';
  function ensureProgress(){
    const panel=document.getElementById('quizPanel');
    if(!panel||panel.querySelector('.s58-progress-wrap'))return;
    const node=document.createElement('div');
    node.className='s58-progress-wrap';
    node.innerHTML='<div class="s58-progress-top"><span id="s58ProgressLabel">تقدم الاختبار</span><span id="s58ProgressCount">١ / ١</span></div><div class="s58-progress-track"><div class="s58-progress-fill" id="s58ProgressFill"></div></div>';
    panel.insertBefore(node,panel.firstChild);
  }
  function ensureTags(){
    const card=document.getElementById('questionCard');
    if(!card||card.querySelector('.s58-question-tags'))return;
    const node=document.createElement('div');node.className='s58-question-tags';node.id='s58QuestionTags';
    const controls=card.querySelector('.question-text-controls');
    if(controls&&controls.nextSibling)card.insertBefore(node,controls.nextSibling);else card.insertBefore(node,card.firstChild);
  }
  function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
  function ar(v){return String(v??'').replace(/[0-9]/g,d=>'٠١٢٣٤٥٦٧٨٩'[Number(d)]);}
  function updateQuestionChrome(){
    ensureProgress();ensureTags();let q=null,total=0,index=0;
    try{if(Array.isArray(activeQuestions)){total=activeQuestions.length;const i=Number.isFinite(Number(activeIndex))?Number(activeIndex):0;index=i+1;q=activeQuestions[i]||null;}}catch(_){ }
    const fill=document.getElementById('s58ProgressFill'),count=document.getElementById('s58ProgressCount'),label=document.getElementById('s58ProgressLabel');
    if(fill)fill.style.width=(total?Math.round(index/total*100):0)+'%';if(count)count.textContent=ar(index+' / '+Math.max(total,1));if(label)label.textContent=q?String(q.exam||'اختبار').replace('قدرات ',''):'تقدم الاختبار';
    const tags=document.getElementById('s58QuestionTags');
    if(tags&&q)tags.innerHTML=`<span class="s58-question-tag">${esc(q.skill||q.category||'قدرات')}</span><span class="s58-question-tag difficulty">${esc(q.difficulty||'متوسط')}</span>`;
    const examLabel=document.getElementById('examLabel');if(examLabel&&q)examLabel.textContent=(q.exam||'قدرات')+' • '+(q.category||'');
    const panel=document.getElementById('quizPanel');if(q&&panel&&!panel.classList.contains('hidden')){const root=document.getElementById('exercisePage'),title=root&&root.querySelector('.page-title'),sub=document.getElementById('exerciseSub');if(title)title.textContent=q.exam==='قدرات كمي'?'اختبار القدرات الكمي':q.exam==='قدرات لفظي'?'اختبار القدرات اللفظي':'اختبار '+String(q.exam||'القدرات');if(sub)sub.textContent='السؤال '+ar(index)+' من '+ar(Math.max(total,1));}
  }
  function patchLoader(){if(typeof window.loadCurrentQuestion!=='function'||window.loadCurrentQuestion.__s58)return;const old=window.loadCurrentQuestion;const fn=function(){const r=old.apply(this,arguments);setTimeout(updateQuestionChrome,0);return r};fn.__s58=true;window.loadCurrentQuestion=fn;}
  function refresh(){document.querySelector('.s58-format-box')?.remove();ensureProgress();ensureTags();patchLoader();updateQuestionChrome();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh,{once:true});else refresh();
  setTimeout(refresh,80);setTimeout(refresh,450);
  new MutationObserver(()=>{document.querySelector('.s58-format-box')?.remove();ensureProgress();ensureTags();}).observe(document.body,{childList:true,subtree:true});
  window.SuhailQuestionBank58={version:VERSION,refresh};
})();
