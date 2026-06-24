/* Sprint 68 - optional result reveal, default OFF. */
(function(){
  'use strict';
  const KEY='suhail_show_answer_result';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  function qNow(){try{return Array.isArray(activeQuestions)?activeQuestions[activeIndex]||null:null}catch(_){return null}}
  function rNow(){try{return Array.isArray(questionResults)?questionResults[activeIndex]||null:null}catch(_){return null}}
  function isOn(){return window.SUHAIL_SHOW_RESULT===true}
  function setOn(v){window.SUHAIL_SHOW_RESULT=!!v;try{localStorage.setItem(KEY,v?'1':'0')}catch(_){};const el=document.getElementById('s68ShowResult');if(el)el.checked=!!v}
  function ensureToggle(){
    const timer=document.querySelector('#setupPanel .timer-card'); if(!timer)return;
    let row=document.getElementById('s68ResultToggle');
    if(!row){row=document.createElement('div');row.id='s68ResultToggle';row.className='s68-result-toggle';row.innerHTML='<div class="s68-result-toggle-title">عرض النتيجة</div><label class="s68-switch"><input id="s68ShowResult" type="checkbox" aria-label="عرض النتيجة"><span class="s68-slider"></span></label>';timer.insertAdjacentElement('afterend',row);row.querySelector('input').addEventListener('change',e=>setOn(e.target.checked));}
    const saved=(()=>{try{return localStorage.getItem(KEY)==='1'}catch(_){return false}})();
    if(typeof window.SUHAIL_SHOW_RESULT!=='boolean')window.SUHAIL_SHOW_RESULT=saved;
    row.querySelector('input').checked=isOn();
  }
  function data(q){const x=q?.explanation;return x&&typeof x==='object'?x:{summary:q?.explain||'',steps:[],similar_choices:[]}}
  function directFeedback(q,selected,correct){
    const x=data(q),mode=String(q?.explanation_mode||'full'),answer=String(q?.answer||q?.choices?.[q?.correct]||''),steps=Array.isArray(x.steps)?x.steps:[],notes=Array.isArray(x.similar_choices)?x.similar_choices:[];
    let html='<div class="s68-direct-feedback">';
    if(!correct) html+='<div class="s68-direct-answer">'+esc(answer)+'</div>';
    if(mode!=='none' && (x.summary||q?.explain)) html+='<div class="s68-direct-text">'+esc(x.summary||q.explain)+'</div>';
    if(mode==='full'&&steps.length) html+='<ol>'+steps.map(s=>'<li>'+esc(s)+'</li>').join('')+'</ol>';
    if(mode==='full'&&x.trap) html+='<div class="s68-direct-note">'+esc(x.trap)+'</div>';
    if(mode==='full'&&!correct){const note=notes.find(n=>Number(n.choice_index)===Number(selected));if(note)html+='<div class="s68-direct-note">'+esc(note.note||'')+'</div>'}
    if(mode==='full'&&q?.hint) html+='<div class="s68-direct-hint">'+esc(q.hint)+'</div>';
    if(correct&&mode==='none') html+='<div class="s68-direct-answer">✓</div>';
    html+='</div>'; return html;
  }
  function paint(q,selected,correct){document.querySelectorAll('#choicesBox .choice').forEach((b,i)=>{b.classList.remove('correct','wrong','s68-selected');if(isOn()){if(i===Number(q.correct))b.classList.add('correct');if(i===Number(selected)&&i!==Number(q.correct))b.classList.add('wrong')}else if(i===Number(selected))b.classList.add('s68-selected')})}
  function sync(){
    ensureToggle(); const q=qNow(),r=rNow(),box=document.getElementById('quizResult'),next=document.getElementById('nextBtn'); if(!q)return;
    if(next)next.disabled=!(r&&r.answered);
    if(!(r&&r.answered)){if(box)box.style.display='none';document.querySelectorAll('#choicesBox .choice').forEach(b=>b.classList.remove('correct','wrong','s68-selected'));return}
    document.querySelectorAll('#choicesBox .choice').forEach(b=>b.disabled=true);paint(q,r.selectedIndex,!!r.correct);
    if(!isOn()){if(box){box.style.display='none';box.innerHTML=''}}else if(box){box.innerHTML=directFeedback(q,r.selectedIndex,!!r.correct);box.style.display='block';box.style.background='transparent';box.style.color='inherit'}
  }
  function answer(button,selected,isCorrect){
    const q=qNow(),r=rNow();if(!q||!r||r.answered)return;
    try{captureQuestionTime()}catch(_){}
    try{isOn()?playAnswerSound(!!isCorrect):playTapSound()}catch(_){}
    r.answered=true;r.correct=!!isCorrect;r.selectedIndex=selected;r.section=q.skill||q.category||currentExam;
    document.querySelectorAll('#choicesBox .choice').forEach(b=>b.disabled=true);
    sync();
    // When result reveal is disabled, keep the test moving without exposing
    // correctness. The index guard prevents a double jump if the student taps
    // Next before this short transition finishes.
    if(!isOn()){
      const answeredIndex=Number(activeIndex);
      setTimeout(()=>{
        try{
          if(examFinished||Number(activeIndex)!==answeredIndex)return;
          if(answeredIndex<activeQuestions.length-1&&typeof nextQuiz==='function')nextQuiz();
        }catch(_){}
      },180);
    }
  }
  answer.__s62=true; answer.__s68=true;
  function patch(){
    window.answerQuiz=answer;
    if(typeof window.loadCurrentQuestion==='function'&&!window.loadCurrentQuestion.__s68){const old=window.loadCurrentQuestion;const fn=function(){const out=old.apply(this,arguments);setTimeout(sync,30);return out};fn.__s68=true;fn.__s62=true;window.loadCurrentQuestion=fn}
    if(typeof window.beginExamWithMode==='function'&&!window.beginExamWithMode.__s68){const old=window.beginExamWithMode;const fn=function(){const el=document.getElementById('s68ShowResult');setOn(!!el?.checked);return old.apply(this,arguments)};fn.__s68=true;window.beginExamWithMode=fn}
    if(typeof window.finishExam==='function'&&!window.finishExam.__s68){const old=window.finishExam;const fn=function(){const out=old.apply(this,arguments);setTimeout(cleanFinal,20);return out};fn.__s68=true;window.finishExam=fn}
  }
  function cleanFinal(){
    document.querySelectorAll('.result-question-card').forEach((card,idx)=>{
      const q=(window.activeQuestions||[])[idx]||{},r=(window.questionResults||[])[idx]||{},lines=[...card.querySelectorAll('.result-answer-line')];
      lines.forEach(x=>x.remove());
      const selected=Number.isInteger(r.selectedIndex)?q.choices?.[r.selectedIndex]:'لم تتم الإجابة';
      card.insertAdjacentHTML('beforeend','<div class="s68-result-choice">'+esc(selected||'')+'</div>');
      if(!r.correct)card.insertAdjacentHTML('beforeend','<div class="s68-result-correct">'+esc(q.answer||q.choices?.[q.correct]||'')+'</div>');
      const x=data(q);if(!r.correct&&(x.summary||q.explain))card.insertAdjacentHTML('beforeend','<div class="s68-result-explain">'+esc(x.summary||q.explain)+'</div>');
    })
  }
  function install(){
    if(typeof window.SUHAIL_SHOW_RESULT!=='boolean'){let v=false;try{v=localStorage.getItem(KEY)==='1'}catch(_){}window.SUHAIL_SHOW_RESULT=v}
    ensureToggle();patch();setInterval(()=>{patch();ensureToggle()},2500);let observerTimer=null;new MutationObserver(()=>{clearTimeout(observerTimer);observerTimer=setTimeout(()=>{patch();ensureToggle()},25)}).observe(document.body,{childList:true,subtree:true});window.SuhailFeedback68={set:setOn,sync};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
