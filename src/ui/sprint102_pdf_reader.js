/* Suhail Sprint 103 — distraction-free PDF reader with OCR text highlighting. */
(function(){
'use strict';
const VERSION='103.0.0';
const PAGES=__S102_PHYSICS1_PAGES__;
const OCR=__S103_PHYSICS1_OCR__;
const KEY='suhail_pdf_text_marks_physics1_v2';
const LAST_KEY='suhail_pdf_last_physics1';
const COLORS=['#ffe66d','#83e6a2','#79c8ff','#ff9fc7'];
let pendingRange=null;
let selectionTimer=0;
let volatileMarks=[];
let volatileLast=1;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function host(){return document.getElementById('summariesPage')}
function readMarks(){try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');volatileMarks=Array.isArray(v)?v:[];return volatileMarks}catch(_){return volatileMarks}}
function writeMarks(list){volatileMarks=Array.isArray(list)?list:[];try{localStorage.setItem(KEY,JSON.stringify(volatileMarks))}catch(_){}}
function readLast(){try{volatileLast=Math.max(1,Number(localStorage.getItem(LAST_KEY)||volatileLast||1));return volatileLast}catch(_){return volatileLast}}
function writeLast(page){volatileLast=Math.max(1,Number(page)||1);try{localStorage.setItem(LAST_KEY,String(volatileLast))}catch(_){}}
function clearSelection(){try{window.getSelection()?.removeAllRanges()}catch(_){}}
function closePalette(){const p=document.querySelector('.s103-selection-palette');if(p)p.classList.remove('show');pendingRange=null}
function back(){
  closePalette();clearSelection();
  document.body.classList.remove('s102-reader-active');
  document.documentElement.classList.remove('s102-reader-active');
  const p=host();if(p){p.classList.remove('s102-reader-host');p.innerHTML=''}
  window.SuhailSummaries101?.renderStages?.('فيزياء');
}
function wordHtml(word,index){
  const [x,y,w,h,text,dir,lineId]=word;
  return `<span class="s103-ocr-word" data-word="${index}" data-line="${esc(lineId||index)}" data-dir="${dir||'rtl'}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}" style="left:${x}%;top:${y}%;width:${w}%;height:${h}%"><span class="s103-ocr-text">${esc(text)}</span></span>`;
}
function pageHtml(src,i){
  const words=Array.isArray(OCR?.[i])?OCR[i]:[];
  return `<section class="s102-page" data-page="${i+1}"><img src="${src}" alt="صفحة ${i+1} من ملخص فيزياء 1" draggable="false"><div class="s102-highlight-layer" data-page="${i+1}"></div><div class="s103-text-layer" data-page="${i+1}" dir="rtl">${words.map(wordHtml).join('')}</div></section>`;
}
function renderMarks(){
  const all=readMarks();
  document.querySelectorAll('.s102-highlight-layer').forEach(layer=>{
    const page=Number(layer.dataset.page);
    layer.innerHTML=all.filter(m=>m.page===page).map(m=>`<i class="s102-highlight" style="left:${m.x}%;top:${m.y}%;width:${m.w}%;height:${m.h}%;background:${m.color}"></i>`).join('');
  });
}
function layoutTextLayer(){
  document.querySelectorAll('.s102-page').forEach(page=>{
    const pr=page.getBoundingClientRect();
    if(!pr.height||!pr.width)return;
    page.querySelectorAll('.s103-ocr-word').forEach(word=>{
      const text=word.querySelector('.s103-ocr-text');if(!text)return;
      const h=Math.max(6,pr.height*(Number(word.dataset.h)||1)/100*.88);
      text.style.fontSize=`${h}px`;
      text.style.transform='none';
      text.style.transformOrigin='center center';
      const target=Math.max(1,word.clientWidth*.96);
      const natural=Math.max(1,text.scrollWidth);
      const scale=Math.max(.48,Math.min(2.5,target/natural));
      text.style.transform=`scaleX(${scale})`;
    });
  });
}
function visiblePage(){
  const pages=[...document.querySelectorAll('.s102-page')];
  let best=0,dist=Infinity;
  pages.forEach((page,i)=>{const d=Math.abs(page.getBoundingClientRect().top);if(d<dist){dist=d;best=i}});
  return best+1;
}
function rememberPage(){writeLast(visiblePage())}
function validSelectionRange(){
  const sel=window.getSelection();
  if(!sel||sel.rangeCount===0||sel.isCollapsed)return null;
  const range=sel.getRangeAt(0);
  const node=range.commonAncestorContainer.nodeType===1?range.commonAncestorContainer:range.commonAncestorContainer.parentElement;
  if(!node?.closest?.('.s103-text-layer'))return null;
  const rects=[...range.getClientRects()].filter(r=>r.width>1&&r.height>1);
  return rects.length?range.cloneRange():null;
}
function selectedWordNodes(range){
  if(!range)return[];
  return [...document.querySelectorAll('.s103-ocr-word')].filter(word=>{
    const node=word.querySelector('.s103-ocr-text')?.firstChild||word;
    try{return range.intersectsNode(node)}catch(_){return false}
  });
}
function showPalette(){
  if(!document.body.classList.contains('s102-reader-active'))return;
  const range=validSelectionRange();
  if(!range){closePalette();return}
  pendingRange=range;
  const words=selectedWordNodes(range);
  const rects=[...range.getClientRects()].filter(r=>r.width>1&&r.height>1);
  const anchor=words.length?words[words.length-1].getBoundingClientRect():rects[rects.length-1];
  if(!anchor)return;
  const palette=document.querySelector('.s103-selection-palette');if(!palette)return;
  palette.classList.add('show');
  const pw=palette.offsetWidth||180,ph=palette.offsetHeight||44;
  let left=anchor.left+anchor.width/2-pw/2;
  left=Math.max(8,Math.min(window.innerWidth-pw-8,left));
  let top=anchor.top-ph-10;
  if(top<8)top=Math.min(window.innerHeight-ph-8,anchor.bottom+10);
  palette.style.left=`${left}px`;palette.style.top=`${top}px`;
}
function queuePalette(delay=180){clearTimeout(selectionTimer);selectionTimer=setTimeout(showPalette,delay)}
function clippedRect(rect,pageRect){
  const left=Math.max(rect.left,pageRect.left),top=Math.max(rect.top,pageRect.top);
  const right=Math.min(rect.right,pageRect.right),bottom=Math.min(rect.bottom,pageRect.bottom);
  if(right-left<1||bottom-top<1)return null;
  return {x:(left-pageRect.left)/pageRect.width*100,y:(top-pageRect.top)/pageRect.height*100,w:(right-left)/pageRect.width*100,h:(bottom-top)/pageRect.height*100};
}
function mergeRects(items){
  const sorted=items.sort((a,b)=>a.page-b.page||a.y-b.y||a.x-b.x),out=[];
  sorted.forEach(r=>{
    const last=out[out.length-1];
    const sameLine=last&&last.page===r.page&&Math.abs(last.y-r.y)<.65&&Math.abs(last.h-r.h)<1.2;
    if(sameLine&&r.x<=last.x+last.w+1.4){
      const right=Math.max(last.x+last.w,r.x+r.w),bottom=Math.max(last.y+last.h,r.y+r.h);
      last.x=Math.min(last.x,r.x);last.y=Math.min(last.y,r.y);last.w=right-last.x;last.h=bottom-last.y;
    }else out.push({...r});
  });
  return out;
}
function applyHighlight(color){
  const range=pendingRange||validSelectionRange();if(!range)return;
  const words=selectedWordNodes(range);
  const pieces=words.map(word=>({
    page:Number(word.closest('.s102-page')?.dataset.page||0),
    line:word.dataset.line||'',
    x:Number(word.dataset.x),y:Number(word.dataset.y),w:Number(word.dataset.w),h:Number(word.dataset.h)
  })).filter(r=>r.page&&Number.isFinite(r.x)&&Number.isFinite(r.y)&&r.w>.05&&r.h>.05);
  const grouped=new Map();
  pieces.forEach(r=>{
    const key=`${r.page}::${r.line}`;
    const old=grouped.get(key);
    if(!old)grouped.set(key,{...r});
    else{
      const right=Math.max(old.x+old.w,r.x+r.w),bottom=Math.max(old.y+old.h,r.y+r.h);
      old.x=Math.min(old.x,r.x);old.y=Math.min(old.y,r.y);old.w=right-old.x;old.h=bottom-old.y;
    }
  });
  const merged=[...grouped.values()];
  if(merged.length){
    const selected=String(window.getSelection()?.toString()||'').trim();
    const all=readMarks(),stamp=Date.now().toString(36);
    merged.forEach((r,i)=>all.push({id:`t${stamp}_${i}`,page:r.page,x:+r.x.toFixed(3),y:+r.y.toFixed(3),w:+r.w.toFixed(3),h:+r.h.toFixed(3),color,text:selected.slice(0,500)}));
    writeMarks(all);renderMarks();
  }
  closePalette();clearSelection();
}
function open(){
  const p=host();if(!p)return;
  document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x===p));
  p.className='page active s102-reader-host';
  document.body.classList.add('s102-reader-active');
  document.documentElement.classList.add('s102-reader-active');
  p.innerHTML=`<div class="s102-reader" role="document" aria-label="ملخص فيزياء 1"><button class="s102-reader-back" aria-label="العودة"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg></button><div class="s102-pages">${PAGES.map(pageHtml).join('')}</div><div class="s103-selection-palette" aria-label="ألوان التظليل">${COLORS.map(c=>`<button type="button" class="s103-palette-color" data-color="${c}" style="--mark:${c}" aria-label="تظليل"></button>`).join('')}</div></div>`;
  const reader=p.querySelector('.s102-reader');
  p.querySelector('.s102-reader-back').onclick=back;
  p.querySelectorAll('.s103-palette-color').forEach(button=>{
    button.addEventListener('pointerdown',e=>e.preventDefault());
    button.addEventListener('click',()=>applyHighlight(button.dataset.color));
  });
  reader.addEventListener('scroll',()=>{rememberPage();closePalette()},{passive:true});
  reader.addEventListener('mouseup',()=>queuePalette(40));
  reader.addEventListener('touchend',()=>queuePalette(320),{passive:true});
  reader.addEventListener('pointerdown',e=>{if(!e.target.closest('.s103-selection-palette'))closePalette()},{passive:true});
  renderMarks();
  requestAnimationFrame(()=>{layoutTextLayer();const last=readLast();p.querySelector(`.s102-page[data-page="${last}"]`)?.scrollIntoView({block:'start'});});
  setTimeout(layoutTextLayer,180);
}
function capture(e){
  const button=e.target.closest('[data-s101-action]');if(!button)return;
  let action='';try{action=decodeURIComponent(button.dataset.s101Action||'')}catch(_){action=button.dataset.s101Action||''}
  if(action==='stage::فيزياء::فيزياء 1'){
    e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();open();
  }
}
function admin(){
  const box=document.getElementById('qmCleanContent');if(!box)return;
  const books=['فيزياء 1','فيزياء 2','فيزياء 3-1','فيزياء 3-2','كيمياء 1','كيمياء 2-1','كيمياء 2-2','كيمياء 3','رياضيات','الأحياء وعلم البيئة'];
  const cards=books.map(book=>`<div class="s102-admin-pdf"><span class="s102-current-badge">${book==='فيزياء 1'?'مركّب — 18 صفحة + طبقة نص':'بانتظار الملف'}</span><h3>${book}</h3><p>ارفع ملف PDF واحدًا. تتم معالجته لإضافة طبقة نص قابلة للتحديد والتظليل، ثم يفتح للطالب في وضع قراءة كامل.</p><input type="file" accept="application/pdf" data-s102-upload="${esc(book)}"><div class="s102-pdf-status"></div></div>`).join('');
  window.qmAppSetPageHeading?.('ملفات الملخصات PDF','إدارة ملف واحد لكل كتاب أو مادة.');
  box.innerHTML=`<div class="app-admin-shell"><button class="app-admin-back" onclick="qmAppRenderContentHome()">رجوع لإدارة المحتوى</button><div class="app-admin-hero"><div class="app-admin-kicker">ملفات الملخصات</div><div class="app-admin-title">إدارة ملفات PDF</div><div class="app-admin-sub">وضع قراءة كامل، طبقة نص، وتظليل محفوظ بأربعة ألوان.</div></div><div class="s102-admin-grid">${cards}</div></div>`;
  box.querySelectorAll('[data-s102-upload]').forEach(input=>input.onchange=()=>{const file=input.files?.[0],status=input.parentElement.querySelector('.s102-pdf-status');if(file)status.textContent=`تم اختيار ${file.name} — سيُعالج لإضافة طبقة النص عند الحفظ.`});
}
function install(){
  document.addEventListener('click',capture,true);
  document.addEventListener('selectionchange',()=>{if(document.body.classList.contains('s102-reader-active'))queuePalette(220)});
  window.addEventListener('resize',()=>{if(document.body.classList.contains('s102-reader-active'))layoutTextLayer()},{passive:true});
  window.s102OpenPhysics1=open;window.qmAppRenderSummaryCurricula=admin;
  window.SuhailPdfReader102={version:VERSION,open,back};window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
