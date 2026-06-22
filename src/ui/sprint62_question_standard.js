/* Sprint 62 — unified bank and educational explanation renderer. */
(function(){
  'use strict';
  const VERSION='62.0.0';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const ar=v=>String(v??'').replace(/[0-9]/g,d=>'٠١٢٣٤٥٦٧٨٩'[Number(d)]);
  function qNow(){try{return Array.isArray(activeQuestions)?activeQuestions[activeIndex]||null:null}catch(_){return null}}
  function resultNow(){try{return Array.isArray(questionResults)?questionResults[activeIndex]||null:null}catch(_){return null}}
  function ensureId(){
    const card=document.getElementById('questionCard'); if(!card)return null;
    let id=card.querySelector('.s62-public-id');
    if(!id){id=document.createElement('div');id.className='s62-public-id';const controls=card.querySelector('.question-text-controls');controls?.insertAdjacentElement('afterend',id);}
    return id;
  }
  function explanationData(q){const x=q?.explanation;return x&&typeof x==='object'?x:{summary:q?.explain||'',steps:[],similar_choices:[]};}
  function renderExplanation(q,selected,correct){
    const x=explanationData(q),steps=Array.isArray(x.steps)?x.steps:[],notes=Array.isArray(x.similar_choices)?x.similar_choices:[];
    const mode=String(q?.explanation_mode||'full');
    const answer=esc(q?.answer||q?.choices?.[q?.correct]||'');
    if(mode==='none'){
      return `<div class="s62-explanation s62-explanation-minimal"><div class="s62-explanation-head"><b>${correct?'إجابة صحيحة':'الإجابة الصحيحة: '+answer}</b><span dir="ltr">سؤال ${esc(q.public_id||'')}</span></div></div>`;
    }
    if(mode==='brief'){
      return `<div class="s62-explanation s62-explanation-brief"><div class="s62-explanation-head"><b>${correct?'أحسنت':'التوضيح'}</b><span dir="ltr">سؤال ${esc(q.public_id||'')}</span></div><p>${esc(x.summary||q.explain||'')}</p></div>`;
    }
    let note=null;
    if(!correct) note=notes.find(n=>Number(n.choice_index)===Number(selected))||null;
    return `<div class="s62-explanation"><div class="s62-explanation-head"><b>${correct?'أحسنت — التوضيح':'الإجابة الصحيحة والتوضيح'}</b><span dir="ltr">سؤال ${esc(q.public_id||'')}</span></div><p>${esc(x.summary||q.explain||'')}</p>${steps.length?`<ol>${steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol>`:''}${x.trap?`<div class="s62-close-choice"><b>انتبه:</b> ${esc(x.trap)}</div>`:''}${note?`<div class="s62-close-choice"><b>لماذا الخيار القريب مختلف؟</b> ${esc(note.note||'')}</div>`:''}${q.hint?`<div class="s62-tip"><b>تلميح سهيل:</b> ${esc(q.hint)}</div>`:''}</div>`;
  }
  function paintCorrect(selected){
    const q=qNow(); if(!q)return;
    document.querySelectorAll('#choicesBox .choice').forEach((b,i)=>{if(i===Number(q.correct))b.classList.add('correct');if(i===Number(selected)&&i!==Number(q.correct))b.classList.add('wrong');});
  }
  function syncQuestion(){
    document.querySelector('.s58-format-box')?.remove();
    const q=qNow(),id=ensureId();
    if(q&&id)id.innerHTML=`رقم السؤال <b dir="ltr">${esc(q.public_id||q.id||'')}</b>`;
    const img=document.getElementById('questionImage'),wrap=document.getElementById('questionImageWrap');
    if(q&&img){img.alt=q.image_alt||'رسم توضيحي للسؤال';img.loading='eager';}
    if(q&&wrap&&!wrap.classList.contains('hidden')){wrap.setAttribute('role','button');wrap.setAttribute('tabindex','0');wrap.setAttribute('aria-label','تكبير صورة السؤال');wrap.onclick=()=>openZoom(img?.src,q.image_alt);wrap.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openZoom(img?.src,q.image_alt)}};}
    const label=document.getElementById('s58ProgressLabel');if(label&&q)label.textContent=String(q.exam||'اختبار').replace('قدرات ','');
    document.querySelectorAll('.s58-question-tag.format').forEach(x=>x.remove());
    const saved=resultNow();if(q&&saved?.answered){const box=document.getElementById('quizResult');if(box){box.innerHTML=renderExplanation(q,saved.selectedIndex,!!saved.correct);box.style.display='block';paintCorrect(saved.selectedIndex);}}
  }
  function ensureZoom(){if(document.getElementById('s62Zoom'))return;const z=document.createElement('div');z.id='s62Zoom';z.className='s62-zoom';z.innerHTML='<div class="s62-zoom-card"><button class="s62-zoom-close" aria-label="إغلاق">×</button><img alt=""></div>';z.onclick=e=>{if(e.target===z||e.target.closest('.s62-zoom-close'))z.classList.remove('open')};document.body.appendChild(z);}
  function openZoom(src,alt){if(!src)return;ensureZoom();const z=document.getElementById('s62Zoom'),img=z.querySelector('img');img.src=src;img.alt=alt||'صورة السؤال';z.classList.add('open');}
  function patch(){
    if(typeof window.loadCurrentQuestion==='function'&&!window.loadCurrentQuestion.__s62){const old=window.loadCurrentQuestion;const fn=function(){const r=old.apply(this,arguments);setTimeout(syncQuestion,20);return r};fn.__s62=true;window.loadCurrentQuestion=fn;}
    if(typeof window.answerQuiz==='function'&&!window.answerQuiz.__s62){const old=window.answerQuiz;const fn=function(button,selected,isCorrect){const r=old.apply(this,arguments);setTimeout(()=>{const q=qNow(),box=document.getElementById('quizResult');if(q&&box){box.innerHTML=renderExplanation(q,selected,!!isCorrect);box.style.display='block';paintCorrect(selected);}},0);return r};fn.__s62=true;window.answerQuiz=fn;}
  }
  function cleanLabels(){document.querySelector('.s58-format-box')?.remove();document.querySelectorAll('.s58-question-tag.format').forEach(x=>x.remove());document.querySelectorAll('.s58-bank-note').forEach(x=>x.remove());}
  function install(){ensureZoom();patch();cleanLabels();syncQuestion();new MutationObserver(()=>{cleanLabels();patch();}).observe(document.body,{childList:true,subtree:true});setInterval(()=>{patch();cleanLabels();},1200);window.SuhailQuestionStandard62={version:VERSION,sync:syncQuestion};window.SUHAIL_RELEASE=VERSION;}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
