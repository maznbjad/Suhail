/* Sprint 58 — computerized Qudurat bank + question presentation */
(function(){
  'use strict';
  const VERSION='58.0.0';
  const FORMAT_KEY='suhail_qudrat_test_format';
  function currentFormat(){
    try{return localStorage.getItem(FORMAT_KEY)||'محوسب';}catch(_){return 'محوسب';}
  }
  function isComputerized(q){
    const value=String((q&& (q.test_format||q.delivery_mode))||'محوسب').toLowerCase();
    return value==='محوسب'||value==='computerized';
  }
  function patchQuestionFilter(){
    if(typeof window.questionsByExam!=='function'||window.questionsByExam.__s58)return;
    const original=window.questionsByExam;
    const wrapped=function(exam){
      const list=original(exam)||[];
      const format=currentFormat();
      if(format==='ورقي') return list.filter(q=>String(q.test_format||'')==='ورقي'||String(q.delivery_mode||'')==='paper');
      return list.filter(isComputerized);
    };
    wrapped.__s58=true;
    window.questionsByExam=wrapped;
  }
  function formatIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 7h8M8 11h3M14 11h2M8 15h3M14 15h2"/></svg>';}
  function paperIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4M9 11h6M9 15h6"/></svg>';}
  function ensureFormatBox(){
    const setup=document.querySelector('#setupPanel .form-box');
    if(!setup||setup.querySelector('.s58-format-box'))return;
    const node=document.createElement('div');
    node.className='s58-format-box';
    node.innerHTML=`<div class="s58-format-label">نمط اختبار القدرات</div>
      <div class="s58-format-grid">
        <button class="s58-format-option active" type="button" aria-pressed="true">${formatIcon()}<span><b>محوسب</b><small>البنك الحالي: أسئلة مهيأة للشاشة</small></span></button>
        <button class="s58-format-option disabled" type="button" disabled aria-disabled="true">${paperIcon()}<span><b>ورقي</b><small>يُفعّل عند إضافة التجميعات الورقية</small></span></button>
      </div>
      <div class="s58-bank-note">اختيار النمط يؤثر في الاختبارات فقط، ولا يغيّر ملخصات الكمي أو اللفظي.</div>`;
    const countCard=setup.querySelector('.setup-single');
    setup.insertBefore(node,countCard||setup.firstChild);
    try{localStorage.setItem(FORMAT_KEY,'محوسب');}catch(_){}
  }
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
    const node=document.createElement('div');
    node.className='s58-question-tags';
    node.id='s58QuestionTags';
    const controls=card.querySelector('.question-text-controls');
    if(controls&&controls.nextSibling)card.insertBefore(node,controls.nextSibling);else card.insertBefore(node,card.firstChild);
  }
  function esc(value){return String(value??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
  function arabicDigits(value){return String(value??'').replace(/[0-9]/g,d=>'٠١٢٣٤٥٦٧٨٩'[Number(d)]);}
  function updateQuestionChrome(){
    ensureProgress();ensureTags();
    let q=null,total=0,index=0;
    try{
      if(typeof activeQuestions!=='undefined'&&Array.isArray(activeQuestions)){
        total=activeQuestions.length;
        const safeIndex=(typeof activeIndex!=='undefined'&&Number.isFinite(Number(activeIndex)))?Number(activeIndex):0;
        index=safeIndex+1;
        q=activeQuestions[safeIndex]||null;
      }
    }catch(_){}
    const fill=document.getElementById('s58ProgressFill');
    const count=document.getElementById('s58ProgressCount');
    const label=document.getElementById('s58ProgressLabel');
    if(fill)fill.style.width=(total?Math.round(index/total*100):0)+'%';
    if(count)count.textContent=arabicDigits(index+' / '+Math.max(total,1));
    if(label)label.textContent=q&&q.exam?String(q.exam).replace('قدرات ','')+' • محوسب':'تقدم الاختبار';
    const tags=document.getElementById('s58QuestionTags');
    if(tags&&q){
      tags.innerHTML=`<span class="s58-question-tag format">محوسب</span><span class="s58-question-tag">${esc(q.skill||q.category||'قدرات')}</span><span class="s58-question-tag difficulty">${esc(q.difficulty||'متوسط')}</span>`;
    }
    const examLabel=document.getElementById('examLabel');
    if(examLabel&&q)examLabel.textContent=(q.exam||'قدرات')+' • '+(q.category||'');
    const quizPanel=document.getElementById('quizPanel');
    if(q&&quizPanel&&!quizPanel.classList.contains('hidden')){
      const pageRoot=document.getElementById('exercisePage');
      const pageTitle=pageRoot&&pageRoot.querySelector('.page-title');
      const pageSub=document.getElementById('exerciseSub');
      if(pageTitle){const title=q.exam==='قدرات كمي'?'اختبار القدرات الكمي':(q.exam==='قدرات لفظي'?'اختبار القدرات اللفظي':'اختبار '+String(q.exam||'القدرات'));pageTitle.textContent=title;}
      if(pageSub)pageSub.textContent='السؤال '+arabicDigits(index)+' من '+arabicDigits(Math.max(total,1))+' • اختر الإجابة ثم تابع';
    }
  }
  function patchLoader(){
    if(typeof window.loadCurrentQuestion!=='function'||window.loadCurrentQuestion.__s58)return;
    const original=window.loadCurrentQuestion;
    const wrapped=function(){const result=original.apply(this,arguments);setTimeout(updateQuestionChrome,0);return result;};
    wrapped.__s58=true;window.loadCurrentQuestion=wrapped;
  }
  function refresh(){patchQuestionFilter();ensureFormatBox();ensureProgress();ensureTags();patchLoader();updateQuestionChrome();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh,{once:true});else refresh();
  setTimeout(refresh,80);setTimeout(refresh,450);
  const observer=new MutationObserver(()=>{ensureFormatBox();ensureProgress();ensureTags();});
  if(document.body)observer.observe(document.body,{childList:true,subtree:true});
  window.SuhailQuestionBank58={version:VERSION,format:currentFormat,refresh};
})();
