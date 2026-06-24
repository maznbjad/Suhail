/* Sprint 69 — summaries become the knowledge source for questions. */
(function(){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const summaries=()=>{try{return Array.isArray(window.smartSummaries)?window.smartSummaries:(typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries:[])}catch(_){return[]}};
  const questionsBank=()=>{try{return Array.isArray(window.questions)?window.questions:(typeof questions!=='undefined'&&Array.isArray(questions)?questions:[])}catch(_){return[]}};
  function findSummary(id){return summaries().find(s=>String(s.summary_id||s.id)===String(id))||null}
  function findBlock(id){for(const s of summaries()){const b=(s.knowledge_blocks||[]).find(x=>String(x.id)===String(id));if(b)return {summary:s,block:b}}return null}
  function refFor(q){if(!q||!q.summary_block_id)return null;const found=findBlock(q.summary_block_id);return found?{...found,question:q}:null}
  function ensureModal(){let m=document.getElementById('s69KnowledgeModal');if(m)return m;m=document.createElement('div');m.id='s69KnowledgeModal';m.className='s69-knowledge-modal';m.innerHTML='<div class="s69-knowledge-sheet" role="dialog" aria-modal="true"><div class="s69-knowledge-head"><span class="s69-knowledge-badge" id="s69KnowledgeBadge">معلومة مرتبطة</span><button class="s69-knowledge-close" onclick="SuhailKnowledge69.close()" aria-label="إغلاق">×</button></div><div class="s69-knowledge-title" id="s69KnowledgeTitle"></div><div class="s69-knowledge-text" id="s69KnowledgeText"></div><div class="s69-knowledge-meta" id="s69KnowledgeMeta"></div><div class="s69-knowledge-actions"><button class="s69-knowledge-primary" id="s69KnowledgeFull">فتح الملخص</button><button class="s69-knowledge-secondary" onclick="SuhailKnowledge69.close()">إغلاق</button></div></div>';m.addEventListener('click',e=>{if(e.target===m)m.classList.remove('open')});document.body.appendChild(m);return m}
  function openBlock(id){const found=findBlock(id);if(!found)return;const {summary:s,block:b}=found;const m=ensureModal();m.querySelector('#s69KnowledgeBadge').textContent=(b.type==='trap'?'فخ شائع':b.type==='definition'?'تعريف':b.type==='rule'?'قانون أو قاعدة':b.type==='tip'?'تلميح سهيل':'معلومة مرتبطة');m.querySelector('#s69KnowledgeTitle').textContent=b.title||s.title;m.querySelector('#s69KnowledgeText').textContent=b.content||'';m.querySelector('#s69KnowledgeMeta').textContent=[s.stage,s.unit,s.title].filter(Boolean).join(' • ');m.querySelector('#s69KnowledgeFull').onclick=()=>{m.classList.remove('open');try{if(typeof s28OpenPhysics==='function')s28OpenPhysics();else if(typeof s59OpenSubject==='function')s59OpenSubject('فيزياء','تحصيلي');else if(typeof openSummarySubject==='function')openSummarySubject('فيزياء')}catch(_){}};m.classList.add('open')}
  function close(){document.getElementById('s69KnowledgeModal')?.classList.remove('open')}
  function decorateCurrent(){
    let q=null;try{q=activeQuestions?.[activeIndex]}catch(_){}
    const box=document.getElementById('questionSummaryLink');if(!box)return;
    if(!q){box.classList.add('hidden');box.removeAttribute('data-s69-signature');return;}
    const r=refFor(q);
    if(!r){box.classList.add('hidden');box.removeAttribute('data-s69-signature');box.onclick=null;return;}
    const {summary:s,block:b}=r;
    const signature=String(q.id||q.public_id||q.question||'')+'::'+String(b.id||'');
    // Mutation observers watch the exam card. Rewriting identical HTML here
    // created a child-list feedback loop for linked Tahsili/physics questions.
    if(box.dataset.s69Signature===signature&&box.querySelector('.s69-knowledge-link')){
      box.classList.remove('hidden');return;
    }
    box.dataset.s69Signature=signature;
    box.innerHTML='<button type="button" class="s69-knowledge-link"><span class="s69-kl-icon">↗</span><span class="s69-kl-copy"><b>'+esc(b.title)+'</b><small>'+esc(s.title+' • '+String(b.content||'').slice(0,85))+'</small></span><em>‹</em></button>';
    box.classList.remove('hidden');box.onclick=()=>openBlock(b.id)
  }
  function questionByText(text){return questionsBank().find(q=>String(q.question||'')===String(text||''))||null}
  const oldToggle=typeof window.toggleHighlight==='function'?window.toggleHighlight:null;
  function enrichedToggle(source,question,answer,note){
    const q=questionByText(question);if(!q||!oldToggle)return oldToggle?oldToggle(source,question,answer,note):'empty';
    let items=[];try{items=JSON.parse(localStorage.getItem('suhail_highlights')||'[]')}catch(_){}
    const idx=items.findIndex(x=>String(x.question)===String(question));
    if(idx>=0){items.splice(idx,1);localStorage.setItem('suhail_highlights',JSON.stringify(items));try{renderHighlights();updateCounts()}catch(_){};return'removed'}
    const exp=q.explanation&&typeof q.explanation==='object'?q.explanation:{};
    items.unshift({id:Date.now(),question_id:q.id,public_id:q.public_id,source:source||q.exam,question:q.question,answer:q.answer||q.choices?.[q.correct]||'',explanation:exp.summary||q.explain||'',note:note||'',summary_id:q.summary_id||'',summary_block_id:q.summary_block_id||'',summary_title:q.summary_title||'',summary_block_title:q.summary_block_title||'',summary_block_excerpt:q.summary_block_excerpt||'',date:new Date().toLocaleDateString('ar-SA')});
    localStorage.setItem('suhail_highlights',JSON.stringify(items));try{renderHighlights();updateCounts()}catch(_){};return'saved'
  }
  function renderSaved(){const list=document.getElementById('highlightList');if(!list)return;let items=[];try{items=JSON.parse(localStorage.getItem('suhail_highlights')||'[]')}catch(_){};const signature=JSON.stringify(items.map(x=>[x.id,x.question_id,x.note,x.summary_block_id]));if(list.dataset.s69Signature===signature)return;list.dataset.s69Signature=signature;if(!items.length){list.innerHTML='<div class="empty-state">لا توجد أسئلة محفوظة حتى الآن.</div>';return}list.innerHTML=items.map(x=>'<article class="mini-card saved-card s69-saved-card"><div class="s69-saved-number">'+(x.public_id?'سؤال '+esc(x.public_id):esc(x.source||''))+' • '+esc(x.date||'')+'</div><div class="s69-saved-question">'+esc(x.question||'')+'</div>'+(x.answer?'<div class="s69-saved-answer">'+esc(x.answer)+'</div>':'')+(x.explanation?'<div class="s69-saved-explain">'+esc(x.explanation)+'</div>':'')+(x.note?'<div class="s69-saved-explain"><b>ملاحظتي:</b> '+esc(x.note)+'</div>':'')+(x.summary_block_id?'<div class="s69-saved-related" onclick="SuhailKnowledge69.open(\''+esc(x.summary_block_id)+'\')"><b>'+esc(x.summary_block_title||'المعلومة المرتبطة')+'</b><span>'+esc(x.summary_block_excerpt||x.summary_title||'')+'</span></div>':'')+'<button class="light-btn" onclick="removeHighlight('+Number(x.id)+')">حذف</button></article>').join('')}

  function currentPhysicsSummary(){
    let subject='',unit='';
    try{subject=String(typeof currentSummarySubject!=='undefined'?currentSummarySubject:'');unit=String(typeof currentSummaryUnit!=='undefined'?currentSummaryUnit:'')}catch(_){}
    if(subject==='فيزياء'&&unit){const hit=summaries().find(x=>String(x.subject)==='فيزياء'&&(String(x.unit)===unit||String(x.title)===unit));if(hit)return hit}
    const visible=[...document.querySelectorAll('#summariesPage .smart-lesson-title,#summariesPage .smart-hero-title,#summariesPage .s59-header h1')].map(x=>String(x.textContent||'').trim()).filter(Boolean);
    return summaries().find(x=>visible.includes(String(x.title||''))||visible.includes(String(x.unit||'')))||null;
  }
  function renderSummaryKnowledge(){
    const page=document.getElementById('summariesPage');if(!page||!page.classList.contains('active'))return;
    const s=currentPhysicsSummary();if(!s||!Array.isArray(s.knowledge_blocks))return;
    const old=page.querySelector('.s69-summary-knowledge');if(old&&old.dataset.summaryId===String(s.summary_id||s.id))return;if(old)old.remove();
    const blocks=s.knowledge_blocks.filter(b=>['idea','definition','rule','trap','tip','example'].includes(b.type)).slice(0,12);
    const target=page.querySelector('.smart-lesson-body')||page.querySelector('#summaryDetail')||page.querySelector('.s59-page')||page;
    const box=document.createElement('section');box.className='s69-summary-knowledge';box.dataset.summaryId=String(s.summary_id||s.id);box.innerHTML='<div class="s69-summary-knowledge-head"><b>جوهر الملخص</b><span>'+Number(s.linked_question_count||0)+' سؤال مرتبط</span></div><div class="s69-summary-blocks">'+blocks.map(b=>'<button type="button" class="s69-summary-block '+(b.is_core?'core ':'')+(b.type==='trap'?'trap':'')+'" onclick="SuhailKnowledge69.open(\''+esc(b.id)+'\')"><h4>'+esc(b.title)+'</h4><p>'+esc(b.content)+'</p><small>'+esc(b.type==='definition'?'تعريف':b.type==='rule'?'قاعدة أو قانون':b.type==='trap'?'فخ شائع':b.type==='tip'?'تلميح سهيل':b.type==='example'?'مثال':'فكرة')+'</small></button>').join('')+'</div>';
    target.appendChild(box);
  }

  function patch(){window.toggleHighlight=enrichedToggle;window.renderHighlights=renderSaved;if(typeof window.loadCurrentQuestion==='function'&&!window.loadCurrentQuestion.__s69){const old=window.loadCurrentQuestion;const fn=function(){const out=old.apply(this,arguments);setTimeout(decorateCurrent,45);return out};fn.__s69=true;window.loadCurrentQuestion=fn}}
  function install(){ensureModal();patch();setInterval(patch,3000);let observerTimer=null;new MutationObserver(()=>{clearTimeout(observerTimer);observerTimer=setTimeout(()=>{patch();if(document.getElementById('questionCard'))decorateCurrent();if(document.getElementById('savedQuestionsPage')?.classList.contains('active'))renderSaved();renderSummaryKnowledge()},20)}).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});setTimeout(()=>{decorateCurrent();renderSaved();renderSummaryKnowledge()},180)}
  window.SuhailKnowledge69={open:openBlock,close,findBlock,refFor};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
