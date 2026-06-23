/* Suhail Sprint 80 — reliable question text scaling and contrast state. */
(function(){
  'use strict';
  const VERSION='80.0.0';
  const KEY='suhail_question_text_size_v2';
  const LEGACY_KEY='suhail_question_text_size';
  const MIN=14,MAX=28,STEP=2,DEFAULT=18;
  let current=DEFAULT;

  function safeGet(key){try{return localStorage.getItem(key);}catch(_){return null;}}
  function safeSet(key,value){try{localStorage.setItem(key,String(value));}catch(_){/* runtime fallback */}}
  function clamp(value){const n=Number(value);return Math.max(MIN,Math.min(MAX,Number.isFinite(n)?n:DEFAULT));}
  function percentage(size){return Math.round((size/DEFAULT)*100);}
  function root(){return document.documentElement;}

  function ensureIndicator(){
    const controls=document.querySelector('#exercisePage .question-text-controls');
    if(!controls)return null;
    let indicator=controls.querySelector('.s80-font-indicator');
    if(!indicator){
      indicator=document.createElement('span');
      indicator.className='s80-font-indicator';
      indicator.id='s80QuestionFontValue';
      indicator.setAttribute('aria-live','polite');
      const buttons=controls.querySelectorAll('.text-size-square');
      if(buttons.length>1)controls.insertBefore(indicator,buttons[1]);else controls.appendChild(indicator);
    }
    return indicator;
  }

  function apply(size,announce){
    current=clamp(size);
    /* The legacy renderer reads a global lexical `questionTextSize` before each
       question. Keep it synchronized so moving to the next question cannot
       restore the old fixed value. */
    try{if(typeof questionTextSize!=='undefined')questionTextSize=current;}catch(_){/* optional legacy binding */}
    const choice=Math.max(MIN,current-1);
    const feedback=Math.max(13,current-4);
    const style=root().style;
    style.setProperty('--s80-font-question',current+'px');
    style.setProperty('--s80-font-choice',choice+'px');
    style.setProperty('--s80-font-passage',choice+'px');
    style.setProperty('--s80-font-feedback',feedback+'px');
    /* Keep legacy variables synchronized for any component that still reads them. */
    style.setProperty('--question-font-size',current+'px');
    style.setProperty('--choice-font-size',choice+'px');
    style.setProperty('--passage-font-size',choice+'px');
    safeSet(KEY,current);safeSet(LEGACY_KEY,current);
    const indicator=ensureIndicator();
    if(indicator){
      indicator.textContent=percentage(current)+'%';
      indicator.setAttribute('aria-label','حجم النص '+percentage(current)+' بالمئة');
    }
    const controls=document.querySelectorAll('#exercisePage .text-size-square');
    if(controls[0])controls[0].disabled=current<=MIN;
    if(controls[1])controls[1].disabled=current>=MAX;
    document.body?.setAttribute('data-s80-font-size',String(current));
    if(announce&&indicator){indicator.animate?.([{transform:'scale(1)'},{transform:'scale(1.08)'},{transform:'scale(1)'}],{duration:180});}
    return current;
  }

  function change(delta){
    try{if(typeof window.playTapSound==='function')window.playTapSound();}catch(_){/* optional */}
    return apply(current+(Number(delta)||0)*STEP,true);
  }
  function reset(){return apply(DEFAULT,true);}

  /* Inline onclick handlers resolve these names at click time, so this final
     ownership replaces the legacy implementation without rewriting the page. */
  window.applyQuestionTextSize=function(size){return apply(size,false);};
  window.changeQuestionTextSize=change;
  window.resetQuestionTextSize=reset;
  window.s80QuestionFont={get:()=>current,set:apply,min:MIN,max:MAX,step:STEP};

  function install(){
    const stored=safeGet(KEY)??safeGet(LEGACY_KEY)??DEFAULT;
    apply(stored,false);
    /* Reapply after every question render, because old modules rebuild controls. */
    if(typeof window.loadCurrentQuestion==='function'&&!window.__s80LoadPatched){
      const original=window.loadCurrentQuestion.bind(window);
      window.loadCurrentQuestion=function(){const result=original.apply(this,arguments);requestAnimationFrame(()=>apply(current,false));return result;};
      window.__s80LoadPatched=true;
    }
    document.addEventListener('click',function(event){
      const button=event.target?.closest?.('#exercisePage .text-size-square');
      if(!button)return;
      requestAnimationFrame(()=>apply(current,false));
    },true);
    window.SUHAIL_RELEASE=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,90));
  else setTimeout(install,90);
})();
