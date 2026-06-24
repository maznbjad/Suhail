/* Suhail Sprint 109 — lightweight multi-book PDF reader, OCR/highlighting removed for performance. */
(function(){
'use strict';
const VERSION='109.0.0';
const BOOK_LIST=__S102_BOOKS__;
const BOOKS=Object.fromEntries((Array.isArray(BOOK_LIST)?BOOK_LIST:[]).map(book=>[book.key,book]));
const STAGE_TO_KEY=Object.fromEntries(Object.values(BOOKS).map(book=>[book.stage,book.key]));
let currentBook=null;
let rememberFrame=0;
let volatileLast=1;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const host=()=>document.getElementById('summariesPage');
const keyFor=suffix=>`suhail_pdf_${suffix}_${currentBook?.key||'unknown'}_v4`;
function readLast(){try{volatileLast=Math.max(1,Number(localStorage.getItem(keyFor('last_page'))||volatileLast||1));return volatileLast}catch(_){return volatileLast}}
function writeLast(page){volatileLast=Math.max(1,Number(page)||1);try{localStorage.setItem(keyFor('last_page'),String(volatileLast))}catch(_){}}
function clearSelection(){try{window.getSelection()?.removeAllRanges()}catch(_){}}
function back(){
  clearSelection();
  document.body.classList.remove('s102-reader-active');
  document.documentElement.classList.remove('s102-reader-active');
  const p=host();if(p){p.classList.remove('s102-reader-host');p.innerHTML=''}
  currentBook=null;
  window.SuhailSummaries101?.renderStages?.('فيزياء');
}
function pageHtml(book,src,i){
  const eager=i<2?'eager':'lazy';
  return `<section class="s102-page" data-page="${i+1}"><img src="${src}" alt="الصفحة ${i+1} من ${esc(book.title)}" loading="${eager}" decoding="async" draggable="false"></section>`;
}
function visiblePage(){
  const reader=document.querySelector('.s102-reader');const rr=reader?.getBoundingClientRect();
  const anchor=(rr?.top||0)+Math.min(90,(rr?.height||0)*.18);
  let best=0,dist=Infinity;
  [...document.querySelectorAll('.s102-page')].forEach((page,i)=>{const d=Math.abs(page.getBoundingClientRect().top-anchor);if(d<dist){dist=d;best=i}});
  return best+1;
}
function rememberPage(){if(rememberFrame)return;rememberFrame=requestAnimationFrame(()=>{rememberFrame=0;writeLast(visiblePage())})}
function openBook(key){
  const book=BOOKS[key];if(!book||!Array.isArray(book.pages)||!book.pages.length)return;
  currentBook=book;volatileLast=1;
  const p=host();if(!p)return;
  document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x===p));p.className='page active s102-reader-host';
  document.body.classList.add('s102-reader-active');document.documentElement.classList.add('s102-reader-active');
  p.innerHTML=`<div class="s102-reader" role="document" aria-label="${esc(book.title)}"><button class="s102-reader-back" type="button" aria-label="العودة إلى كتب الفيزياء"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg></button><div class="s102-pages">${book.pages.map((src,i)=>pageHtml(book,src,i)).join('')}</div></div>`;
  const reader=p.querySelector('.s102-reader');p.querySelector('.s102-reader-back').onclick=back;
  reader.addEventListener('scroll',rememberPage,{passive:true});
  requestAnimationFrame(()=>{const last=Math.min(book.pages.length,readLast());p.querySelector(`.s102-page[data-page="${last}"]`)?.scrollIntoView({block:'start'})});
}
function capture(e){
  const button=e.target.closest('[data-s101-action]');if(!button)return;
  let action='';try{action=decodeURIComponent(button.dataset.s101Action||'')}catch(_){action=button.dataset.s101Action||''}
  const parts=action.split('::');if(parts[0]!=='stage')return;
  const stage=parts[2]||'',key=STAGE_TO_KEY[stage];if(!key)return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();openBook(key);
}
function admin(){
  const box=document.getElementById('qmCleanContent');if(!box)return;
  const expected=['فيزياء 1','فيزياء 2','فيزياء 3-1','فيزياء 3-2','كيمياء 1','كيمياء 2-1','كيمياء 2-2','كيمياء 3','رياضيات','الأحياء وعلم البيئة'];
  const byStage=Object.fromEntries(Object.values(BOOKS).map(book=>[book.stage,book]));
  const cards=expected.map(stage=>{const book=byStage[stage],installed=!!book;return `<div class="s102-admin-pdf"><span class="s102-current-badge ${installed?'':'waiting'}">${installed?`مركّب — ${book.pageCount} صفحة`:'بانتظار الملف'}</span><h3>${esc(stage)}</h3><p>ملف PDF واحد لكل كتاب. يظهر للطالب بوضع قراءة كامل وخفيف بدون OCR أو تظليل نصي.</p><input type="file" accept="application/pdf" data-s102-upload="${esc(stage)}"><div class="s102-pdf-status"></div></div>`}).join('');
  window.qmAppSetPageHeading?.('ملفات الملخصات PDF','إدارة ملف واحد لكل كتاب أو مادة.');
  box.innerHTML=`<div class="app-admin-shell"><button class="app-admin-back" onclick="qmAppRenderContentHome()">رجوع لإدارة المحتوى</button><div class="app-admin-hero"><div class="app-admin-kicker">ملفات الملخصات</div><div class="app-admin-title">إدارة ملفات PDF</div><div class="app-admin-sub">وضع قراءة كامل وخفيف، بدون OCR أو تظليل نصي لتحسين السرعة.</div></div><div class="s102-admin-grid">${cards}</div></div>`;
  box.querySelectorAll('[data-s102-upload]').forEach(input=>input.onchange=()=>{const file=input.files?.[0],status=input.parentElement.querySelector('.s102-pdf-status');if(file)status.textContent=`تم اختيار ${file.name} — سيُركّب كملف قراءة خفيف.`});
}
function getBook(value){return BOOKS[value]||BOOKS[STAGE_TO_KEY[value]]||null}
function install(){
  document.addEventListener('click',capture,true);
  window.s102OpenPhysics1=()=>openBook('physics1');window.s102OpenBook=openBook;window.qmAppRenderSummaryCurricula=admin;
  window.SuhailPdfReader102={version:VERSION,openBook,back,getBook,books:BOOKS};window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
