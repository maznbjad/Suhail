/* Sprint 69 — exact knowledge linking for the approved physics summaries. */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
  function summariesBank(){try{return Array.isArray(smartSummaries)?smartSummaries:[]}catch(_){return[]}}
  function questionBank(){try{return Array.isArray(questions)?questions:[]}catch(_){return[]}}
  function summaryById(id){return summariesBank().find(s=>String(s.id||s.summary_id)===String(id||''))||null}
  function blockById(summary,id){return (summary?.knowledge_blocks||[]).find(b=>String(b.id)===String(id||''))||null}
  function questionByKey(key){return questionBank().find(q=>String(q.id)===String(key)||String(q.public_id)===String(key)||String(q.question)===String(key))||null}
  function currentQuestion(){try{return Array.isArray(activeQuestions)?activeQuestions[activeIndex]||null:null}catch(_){return null}}
  function exactRef(q){if(!q||!q.summary_id)return null;const s=summaryById(q.summary_id);if(!s)return null;const b=blockById(s,q.summary_block_id);return {exam:'تحصيلي',subject:'فيزياء',stage:s.stage,unit:s.unit,lesson:s.title,summary_id:s.id,block_id:b?.id||'',block_title:b?.title||q.linked_block_title||'',block_content:b?.content||q.linked_block_excerpt||'',summary:s,block:b}}
  const oldRef=typeof window.getQuestionSummaryRef==='function'?window.getQuestionSummaryRef:null;
  window.getQuestionSummaryRef=function(q){return exactRef(q)||(oldRef?oldRef(q):null)};

  function injectKnowledgeCard(ref){
    if(!ref)return;
    const body=document.querySelector('#summariesPage .s14-body');if(!body)return;
    body.querySelector('.s69-knowledge-card')?.remove();
    const card=document.createElement('section');card.className='s69-knowledge-card s69-flash';card.id='s69KnowledgeTarget';
    card.innerHTML=`<div class="s69-knowledge-label">المعلومة المرتبطة بالسؤال</div><div class="s69-knowledge-title">${esc(ref.block_title||ref.lesson)}</div><div class="s69-knowledge-text">${esc(ref.block_content||ref.summary?.simple_idea||'')}</div><div class="s69-knowledge-lesson">${esc(ref.stage)} • ${esc(ref.unit)} • ${esc(ref.lesson)}</div>`;
    const anchor=body.querySelector('.s14-title-row');if(anchor)anchor.insertAdjacentElement('afterend',card);else body.prepend(card);
    setTimeout(()=>card.scrollIntoView({behavior:'smooth',block:'center'}),100);
  }
  window.s69OpenKnowledge=function(summaryId,blockId){
    const s=summaryById(summaryId);if(!s)return;
    const b=blockById(s,blockId);
    const ref={stage:s.stage,unit:s.unit,lesson:s.title,summary:s,block:b,block_title:b?.title||'',block_content:b?.content||''};
    try{localStorage.setItem('s69_pending_knowledge',JSON.stringify({summaryId,blockId}))}catch(_){}
    if(typeof window.s17OpenUnit==='function')window.s17OpenUnit(encodeURIComponent(s.stage||''),encodeURIComponent(s.unit||''));
    else if(typeof window.s59OpenSubject==='function')window.s59OpenSubject('فيزياء','تحصيلي');
    let tries=0;const timer=setInterval(()=>{tries++;const page=document.querySelector('#summariesPage .s14-body');if(page){clearInterval(timer);injectKnowledgeCard(ref)}else if(tries>30)clearInterval(timer)},100);
  };
  function restorePending(){let p=null;try{p=JSON.parse(localStorage.getItem('s69_pending_knowledge')||'null')}catch(_){};if(!p)return;const s=summaryById(p.summaryId);if(!s)return;const b=blockById(s,p.blockId);if(document.querySelector('#summariesPage .s14-body')){injectKnowledgeCard({stage:s.stage,unit:s.unit,lesson:s.title,summary:s,block:b,block_title:b?.title||'',block_content:b?.content||''});try{localStorage.removeItem('s69_pending_knowledge')}catch(_){}}}

  function syncQuestionLink(){
    const q=currentQuestion(),el=document.getElementById('questionSummaryLink');if(!el)return;
    const ref=exactRef(q),r=(()=>{try{return questionResults?.[activeIndex]}catch(_){return null}})();
    const allowed=!!(ref&&r?.answered&&window.SUHAIL_SHOW_RESULT===true);
    if(!allowed){el.classList.add('hidden');el.innerHTML='';el.onclick=null;return}
    el.className='question-summary-link s69-question-link';
    el.innerHTML=`<span><b>راجع المعلومة</b><small>${esc(ref.block_title||ref.lesson)}</small></span><span class="s69-go">‹</span>`;
    el.onclick=()=>window.s69OpenKnowledge(ref.summary_id,ref.block_id);
  }

  function richSave(q){
    const items=(()=>{try{return JSON.parse(localStorage.getItem('suhail_highlights')||'[]')}catch(_){return[]}})();
    const key=String(q.id||q.public_id||q.question);const idx=items.findIndex(x=>String(x.question_id||x.question)===key||x.question===q.question);
    if(idx>=0){items.splice(idx,1);localStorage.setItem('suhail_highlights',JSON.stringify(items));return 'removed'}
    const ref=exactRef(q),x=(q.explanation&&typeof q.explanation==='object')?q.explanation:{summary:q.explain||''};
    items.unshift({id:Date.now(),question_id:key,public_id:q.public_id||'',source:q.exam||currentExam,question:q.question||'',answer:q.answer||q.choices?.[q.correct]||'',explanation:x.summary||q.explain||'',note:(typeof getNote==='function'?getNote(q.question):''),date:new Date().toLocaleDateString('ar-SA'),summary_id:q.summary_id||'',summary_block_id:q.summary_block_id||'',linked_block_title:ref?.block_title||'',linked_block_excerpt:ref?.block_content||''});
    localStorage.setItem('suhail_highlights',JSON.stringify(items));return 'saved';
  }
  window.toggleCurrentQuiz=function(){const q=currentQuestion();if(!q)return;const status=richSave(q);if(status==='saved')markQuizSaved?.();else resetQuizSaved?.();renderHighlights?.();updateCounts?.();const result=document.getElementById('quizResult');if(result){result.style.display='block';result.style.background=status==='saved'?'#ecfdf3':'#f6f8fa';result.style.color=status==='saved'?'#166534':'#526170';result.innerHTML=status==='saved'?'تم حفظ السؤال':'تم إلغاء حفظ السؤال'}};

  window.renderHighlights=function(){
    const list=document.getElementById('highlightList');if(!list)return;let items=[];try{items=JSON.parse(localStorage.getItem('suhail_highlights')||'[]')}catch(_){}
    if(!items.length){list.innerHTML='<div class="empty-state">لا توجد أسئلة محفوظة حتى الآن.</div>';return}
    list.innerHTML=items.map(item=>{const q=questionByKey(item.question_id)||questionByKey(item.public_id)||null;const ref=q?exactRef(q):(item.summary_id?{summary_id:item.summary_id,block_id:item.summary_block_id,block_title:item.linked_block_title,block_content:item.linked_block_excerpt}:null);const answer=item.answer||q?.answer||'';const explanation=item.explanation||q?.explanation?.summary||q?.explain||'';return `<article class="s69-saved-card"><div class="s69-saved-top"><span>${esc(item.source||q?.exam||'سؤال')}</span><span>${item.public_id?`#${esc(item.public_id)}`:esc(item.date||'')}</span></div><div class="s69-saved-q">${esc(item.question||q?.question||'')}</div>${answer?`<div class="s69-saved-answer">${esc(answer)}</div>`:''}${explanation?`<div class="s69-saved-explain">${esc(explanation)}</div>`:''}${item.note?`<div class="s69-saved-note">${esc(item.note)}</div>`:''}${ref?.summary_id?`<button class="s69-saved-link" onclick="s69OpenKnowledge('${esc(ref.summary_id)}','${esc(ref.block_id||'')}')"><span><span class="s69-linked-badge">مرتبط بالملخص</span><br>${esc(ref.block_title||'راجع المعلومة')}</span><b>‹</b></button>`:''}<div class="s69-saved-actions"><button class="s69-saved-delete" onclick="removeHighlight(${Number(item.id)||0})">حذف</button></div></article>`}).join('');
  };

  function patch(){
    if(typeof window.loadCurrentQuestion==='function'&&!window.loadCurrentQuestion.__s69){const old=window.loadCurrentQuestion;const fn=function(){const out=old.apply(this,arguments);setTimeout(syncQuestionLink,50);return out};fn.__s69=true;window.loadCurrentQuestion=fn}
    if(window.SuhailFeedback68?.sync&&!window.SuhailFeedback68.sync.__s69){const old=window.SuhailFeedback68.sync;const fn=function(){const out=old.apply(this,arguments);setTimeout(syncQuestionLink,20);return out};fn.__s69=true;window.SuhailFeedback68.sync=fn}
  }
  function install(){patch();renderHighlights?.();setInterval(()=>{patch();syncQuestionLink();restorePending()},700);new MutationObserver(()=>{patch();restorePending()}).observe(document.body,{childList:true,subtree:true});window.SUHAIL_KNOWLEDGE_RELEASE='69.0.0'}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
