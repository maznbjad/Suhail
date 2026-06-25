/* Suhail Sprint 110 — focused student experience and performance-first evaluation. */
(function(){
'use strict';
const VERSION='110.0.0';
let installed=false,rendering=false,observerTimer=0;
const TRACKS=['قدرات كمي','قدرات لفظي','تحصيلي'];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>({
  home:'<svg viewBox="0 0 24 24"><path d="m3 10 9-7 9 7"/><path d="M5 9v11h14V9M9 20v-6h6v6"/></svg>',
  summary:'<svg viewBox="0 0 24 24"><path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
  collection:'<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="3"/><path d="M8 9h8M8 13h5"/></svg>',
  performance:'<svg viewBox="0 0 24 24"><path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/></svg>',
  next:'<svg viewBox="0 0 24 24"><path d="M5 12h13M14 7l5 5-5 5"/><circle cx="6" cy="12" r="3"/></svg>',
  account:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  back:'<svg viewBox="0 0 24 24"><path d="m9 5 7 7-7 7"/></svg>'
}[name]||'');
function session(){try{return typeof getAuthSession==='function'?getAuthSession():JSON.parse(localStorage.getItem('suhail_auth_user')||'null')}catch(_){return null}}
function userKey(){const email=String(session()?.email||'guest').toLowerCase();return email.replace(/[^a-z0-9]/g,'_')||'guest'}
function storageGet(k,f=''){try{const v=localStorage.getItem(k);return v==null?f:v}catch(_){return f}}
function storageSet(k,v){try{localStorage.setItem(k,v);return true}catch(_){return false}}
function isDark(){return storageGet('s55_theme','light')==='dark'}
function history(){try{if(typeof getExamHistory==='function')return getExamHistory()||[];return JSON.parse(localStorage.getItem(`suhail_exam_history_${userKey()}`)||'[]')}catch(_){return[]}}
function challengeHistory(){try{const rows=JSON.parse(localStorage.getItem('suhail_group_challenge_history')||'[]');return Array.isArray(rows)?rows:[]}catch(_){return[]}}
function questionsList(){try{return Array.isArray(questions)?questions:[]}catch(_){return[]}}
function clamp(v){return Math.max(0,Math.min(100,Math.round(Number(v)||0)))}
function avg(arr){return arr.length?arr.reduce((a,b)=>a+Number(b||0),0)/arr.length:0}
function trackStats(exam){
  const rows=history().filter(x=>String(x.exam||'')===exam);
  const total=rows.reduce((a,x)=>a+Number(x.total||0),0),correct=rows.reduce((a,x)=>a+Number(x.correct||0),0);
  const accuracy=total?Math.round(correct/total*100):0;
  return {exam,rows,total,correct,accuracy,last:rows[0]?.percent||0,best:rows.length?Math.max(...rows.map(x=>Number(x.percent||0))):0,attempts:rows.length,avgSec:Math.round(avg(rows.map(x=>x.avgSec).filter(Boolean)))};
}
function snapshot(){
  const rows=history(),tracks=TRACKS.map(trackStats),total=rows.reduce((a,x)=>a+Number(x.total||0),0),correct=rows.reduce((a,x)=>a+Number(x.correct||0),0);
  const accuracy=total?Math.round(correct/total*100):0;
  const recent=rows.slice(0,6).map(x=>Number(x.percent||0));
  const spread=recent.length>1?Math.sqrt(avg(recent.map(v=>Math.pow(v-avg(recent),2)))):0;
  const stability=recent.length>1?clamp(100-spread*2.7):(rows.length?60:0);
  const coverage=clamp(tracks.filter(x=>x.attempts).length/3*100);
  const speed=Math.round(avg(rows.map(x=>x.avgSec).filter(Boolean)))||0;
  const speedScore=speed?clamp(100-Math.max(0,speed-60)*1.2):0;
  const readiness=rows.length?clamp(accuracy*.62+stability*.18+coverage*.12+speedScore*.08):0;
  const started=tracks.filter(x=>x.attempts);const weakest=(started.length?started:tracks).slice().sort((a,b)=>a.accuracy-b.accuracy||a.attempts-b.attempts)[0];
  return {rows,tracks,total,correct,accuracy,stability,coverage,speed,readiness,weakest};
}
function level(score){score=Number(score)||0;if(!history().length)return {label:'ابدأ القياس',text:'أول اختبار قصير يبني لك تقييمًا واضحًا.'};if(score<45)return {label:'يحتاج تأسيس',text:'ابدأ بالأساسيات ثم حل عددًا قليلًا من الأسئلة.'};if(score<65)return {label:'يتحسن',text:'راجع الأخطاء المتكررة وركز على أضعف مسار.'};if(score<80)return {label:'جيد',text:'مستواك جيد؛ ثبّت السرعة وقلل الأخطاء البسيطة.'};if(score<90)return {label:'قريب من الهدف',text:'ركز على المسار الأضعف لرفع جاهزيتك.'};return {label:'متقن',text:'حافظ على المستوى باختبارات قصيرة ومتنوعة.'}}
function profile(){const s=session()||{};return {name:s.name||s.display_name||'طالب سهيل',username:String(s.username||String(s.email||'student').split('@')[0]||'student').replace(/^@/,''),role:s.role||'student'}}
function ensurePage(id){let p=document.getElementById(id);if(!p){p=document.createElement('div');p.id=id;p.className='page';document.querySelector('.content')?.appendChild(p)}return p}
function activate(id){document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p.id===id));const scroller=document.querySelector('.content');if(scroller)scroller.scrollTop=0;syncNav(id);document.body.classList.toggle('s110-exam-active',id==='exercisePage');}
function top(title,sub,back){return `<div class="s110-top">${back?`<button class="s110-back" type="button" onclick="${back}" aria-label="العودة">${icon('back')}</button>`:`<button class="s110-profile-button" type="button" onclick="showPage('profilePage')" aria-label="الحساب">${esc((profile().name||'س').trim().charAt(0)||'س')}</button>`}<div class="s110-top-copy"><h1>${esc(title)}</h1>${sub?`<p>${esc(sub)}</p>`:''}</div></div>`}
function actionForExam(exam){return `openExamSetup('${String(exam).replace(/'/g,"\\'")}')`}
function nextStepData(){
  const s=snapshot(),w=s.weakest;
  if(!s.rows.length)return {title:'ابدأ بقياس قصير',detail:'حل 10 أسئلة لنبني أول تقييم لمستواك.',exam:'قدرات كمي',count:10,minutes:10,reason:'بناء خط البداية'};
  if(w.accuracy<60)return {title:`راجع ${w.exam}`,detail:`دقتك الحالية ${w.accuracy}%. ابدأ بـ10 أسئلة مركزة ثم راجع الأخطاء.`,exam:w.exam,count:10,minutes:12,reason:'أضعف مسار'};
  if(s.speed>75)return {title:`ارفع السرعة في ${w.exam}`,detail:`متوسطك ${s.speed} ثانية للسؤال. نفّذ اختبارًا قصيرًا بوقت محدد.`,exam:w.exam,count:10,minutes:10,reason:'تحسين السرعة'};
  return {title:`ثبّت ${w.exam}`,detail:`نتيجتك ${w.accuracy}%. اختبار قصير يحافظ على الثبات ويكشف الأخطاء البسيطة.`,exam:w.exam,count:10,minutes:10,reason:'تثبيت الأداء'};
}
function renderHome(){
  const p=ensurePage('homePage'),s=snapshot(),l=level(s.readiness),step=nextStepData();rendering=true;
  p.innerHTML=`<div class="s110-page" data-s110-page="home" data-s54-home="1">${top(`مرحبًا، ${profile().name.split(' ')[0]||'طالب'}`,'ركز على ما يرفع مستواك فقط')}
    <section class="s110-readiness"><div class="s110-readiness-row"><div class="s110-readiness-copy"><div class="s110-eyebrow">تقييم الأداء</div><h2>${esc(l.label)}</h2><p>${esc(l.text)}${s.weakest?.attempts?` أضعف مسار: ${esc(s.weakest.exam)}.`:''}</p></div><div class="s110-ring" style="--p:${s.readiness}"><b>${s.rows.length?s.readiness:'—'}<span>${s.rows.length?'%':''}</span></b></div></div><button class="s110-readiness-action" onclick="showPage('statsPage')">عرض تقرير الأداء</button></section>
    <div class="s110-section-head"><b>كل ما تحتاجه</b><span>4 أقسام فقط</span></div>
    <div class="s110-core-grid">
      <button class="s110-core-card" onclick="showPage('summariesPage')"><i class="s110-core-icon">${icon('summary')}</i><b>الملخصات</b><span>ملفات المواد بوضع قراءة كامل.</span><em>قراءة سريعة</em></button>
      <button class="s110-core-card collections" onclick="showPage('collectionsPage')"><i class="s110-core-icon">${icon('collection')}</i><b>التجميعات</b><span>اختبارات القدرات والتحصيلي من مكان واحد.</span><em>${questionsList().length} سؤال</em></button>
      <button class="s110-core-card performance" onclick="showPage('statsPage')"><i class="s110-core-icon">${icon('performance')}</i><b>تقارير الأداء</b><span>دقتك، سرعتك، ثباتك ونقاط التحسن.</span><em>${s.rows.length} محاولة</em></button>
      <button class="s110-core-card next" onclick="showPage('nextStepPage')"><i class="s110-core-icon">${icon('next')}</i><b>خطوتي المختصرة</b><span>مهمة واحدة فقط مبنية على مستواك الحالي.</span><em>${esc(step.exam)}</em></button>
    </div>
    <div class="s110-next-strip"><div><b>${esc(step.title)}</b><span>${esc(step.detail)}</span></div><button onclick="showPage('nextStepPage')">ابدأ</button></div>
  </div>`;rendering=false;activate('homePage');
}
function renderCollections(){
  const p=ensurePage('collectionsPage');const qs=questionsList();const count=e=>qs.filter(q=>String(q.exam||q.type||'')===e).length;
  p.innerHTML=`<div class="s110-page" data-s110-page="collections">${top('التجميعات','اختر المسار وابدأ مباشرة',"showPage('homePage')")}
    <div class="s110-collection-list">${TRACKS.map((e,i)=>`<article class="s110-collection-card"><div class="s110-collection-icon">${i===0?'∑':i===1?'أ':'⚛'}</div><div class="s110-collection-copy"><b>${esc(e)}</b><span>${count(e)} سؤال متاح • يحفظ الأداء تلقائيًا</span></div><button onclick="${actionForExam(e)}">ابدأ</button></article>`).join('')}<article class="s110-collection-card"><div class="s110-collection-icon">🏆</div><div class="s110-collection-copy"><b>تحدي جماعي</b><span>حتى 10 لاعبين • 30 ثانية للسؤال • أول صحيح يكسب</span></div><button onclick="s113OpenChallenges()">فتح</button></article></div>
    <div class="s110-section-head"><b>بعد كل اختبار</b></div><div class="s110-empty">تُضاف النتيجة مباشرة إلى تقرير الأداء، ويحدد سهيل المسار الأضعف والخطوة التالية.</div>
  </div>`;activate('collectionsPage');
}
function renderPerformance(){
  const p=ensurePage('statsPage'),s=snapshot(),l=level(s.readiness),step=nextStepData(),challengeRows=challengeHistory(),challengeAvg=challengeRows.length?Math.round(avg(challengeRows.map(x=>Number(x.avgMs||0)).filter(Boolean))/1000):0;
  p.innerHTML=`<div class="s110-page" data-s110-page="performance">${top('أدائي','تقييم واضح بدون أرقام مشتتة',"showPage('homePage')")}
    <section class="s110-readiness"><div class="s110-readiness-row"><div class="s110-readiness-copy"><div class="s110-eyebrow">جاهزيتك الحالية</div><h2>${esc(l.label)}</h2><p>${esc(l.text)}</p></div><div class="s110-ring" style="--p:${s.readiness}"><b>${s.rows.length?s.readiness:'—'}<span>${s.rows.length?'%':''}</span></b></div></div></section>
    <div class="s110-section-head"><b>المؤشرات الأساسية</b></div><div class="s110-metrics"><div class="s110-metric"><b>${s.total||0}</b><span>سؤال محلول</span></div><div class="s110-metric"><b>${s.rows.length?s.accuracy+'%':'—'}</b><span>الدقة العامة</span></div><div class="s110-metric"><b>${s.speed||'—'}</b><span>ثانية لكل سؤال</span></div><div class="s110-metric"><b>${s.rows.length}</b><span>اختبار مكتمل</span></div></div>
    <div class="s110-section-head"><b>تقييم المسارات</b><span>الأضعف أولًا</span></div><div class="s110-track-list">${s.tracks.slice().sort((a,b)=>a.accuracy-b.accuracy).map(t=>`<article class="s110-track"><div class="s110-track-top"><b>${esc(t.exam)}</b><strong>${t.attempts?t.accuracy+'%':'—'}</strong></div><div class="s110-track-bar"><i style="width:${t.accuracy}%"></i></div><small>${t.attempts?`${t.attempts} محاولات • أفضل نتيجة ${t.best}%${t.avgSec?` • ${t.avgSec}ث/سؤال`:''}`:'لم تبدأ بعد'}</small></article>`).join('')}</div>
    <div class="s110-section-head"><b>قرار سهيل</b></div><section class="s110-assessment"><b>${esc(step.title)}</b><p>${esc(step.detail)}</p><button onclick="showPage('nextStepPage')">تنفيذ الخطوة المختصرة</button></section>
    ${challengeRows.length?`<div class="s110-section-head"><b>أداء التحديات</b><span>${challengeRows.length} تحديات</span></div><div class="s110-metrics"><div class="s110-metric"><b>${challengeRows.filter(x=>Number(x.rank)===1).length}</b><span>مركز أول</span></div><div class="s110-metric"><b>${challengeAvg||'—'}</b><span>ث/إجابة حاسمة</span></div><div class="s110-metric"><b>${Math.round(avg(challengeRows.map(x=>Number(x.score||0))))}</b><span>متوسط النقاط</span></div><div class="s110-metric"><b>${Math.round(avg(challengeRows.map(x=>Number(x.players||0))))}</b><span>متوسط اللاعبين</span></div></div>`:''}
    <div class="s110-section-head"><b>آخر النتائج</b><span>${Math.min(5,s.rows.length)} نتائج</span></div><div class="s110-history">${s.rows.length?s.rows.slice(0,5).map(r=>`<div class="s110-history-row"><div><b>${esc(r.exam||'اختبار')}</b><span>${esc(r.dateLabel||new Date(r.date||r.id||Date.now()).toLocaleDateString('ar-SA'))} • ${Number(r.correct||0)}/${Number(r.total||0)}</span></div><strong>${Number(r.percent||0)}%</strong></div>`).join(''):'<div class="s110-empty">لا توجد نتائج بعد. ابدأ من التجميعات ليظهر تقييمك هنا.</div>'}</div>
  </div>`;activate('statsPage');
}
function renderNext(){
  const p=ensurePage('nextStepPage'),s=snapshot(),step=nextStepData();
  p.innerHTML=`<div class="s110-page" data-s110-page="next">${top('خطوتي المختصرة','مهمة واحدة؛ ثم قياس النتيجة',"showPage('homePage')")}
    <section class="s110-step-card"><div class="s110-step-number">1</div><h2>${esc(step.title)}</h2><p>${esc(step.detail)}</p><div class="s110-step-meta"><div><b>${step.count}</b><span>أسئلة</span></div><div><b>${step.minutes}</b><span>دقائق</span></div><div><b>${s.weakest?.accuracy||0}%</b><span>دقة المسار</span></div></div><button class="s110-step-main" onclick="${actionForExam(step.exam)}">ابدأ ${esc(step.exam)}</button></section>
    <div class="s110-section-head"><b>لماذا هذه الخطوة؟</b></div><div class="s110-empty">${esc(step.reason)}. بعد إنهائها يتحدث تقرير الأداء تلقائيًا، ثم يعطيك سهيل خطوة جديدة.</div>
  </div>`;activate('nextStepPage');
}
function renderAccount(){
  const p=ensurePage('profilePage'),u=profile(),dark=isDark();
  p.innerHTML=`<div class="s110-page" data-s110-page="account">${top('الحساب','الإعدادات الأساسية فقط',"showPage('homePage')")}
    <section class="s110-account-card"><div class="s110-avatar">${esc((u.name||'س').trim().charAt(0)||'س')}</div><div class="s110-account-copy"><b>${esc(u.name)}</b><span>@${esc(u.username)}</span></div></section>
    <div class="s110-settings"><div class="s110-setting"><b>الوضع الداكن</b><button class="s110-theme-toggle ${dark?'on':''}" onclick="s110ToggleTheme(event)" aria-label="تبديل الوضع الداكن"><i></i></button></div><button class="s110-setting" onclick="s112OpenFriends()"><b>الأصدقاء</b><span>إضافة باليوزر فقط</span></button><button class="s110-setting" onclick="s113OpenChallenges()"><b>التحديات الجماعية</b><span>حتى 10 لاعبين</span></button><button class="s110-setting" onclick="showPage('supportPage')"><b>تواصل معنا</b><span>اقتراح أو بلاغ</span></button><button class="s110-setting" onclick="s114OpenLegal()"><b>الخصوصية والشروط</b><span>الشروط، الخصوصية وحذف الحساب</span></button>${u.role==='admin'?`<button class="s110-setting s110-admin-link" onclick="showPage('questionManagementPage')"><b>إدارة المحتوى</b><span>الملخصات والتجميعات</span></button>`:''}<button class="s110-setting danger" onclick="logoutUser()"><b>تسجيل الخروج</b><span></span></button></div>
  </div>`;activate('profilePage');
}
function renderSupport(){
  const p=ensurePage('supportPage');p.innerHTML=`<div class="s110-page" data-s110-page="support">${top('تواصل معنا','اقتراح أو بلاغ عن مشكلة',"showPage('profilePage')")}<section class="s110-assessment"><b>رسالتك تهمنا</b><p>اكتب الملاحظة باختصار، وستُحفظ على الجهاز في هذه النسخة.</p><textarea id="s110SupportText" style="width:100%;min-height:120px;margin-top:12px;border:1px solid var(--s110-border);border-radius:14px;background:var(--s110-card);color:var(--s110-text);padding:12px;font:750 12px 'Tajawal';resize:vertical" placeholder="اكتب اقتراحك أو المشكلة..."></textarea><button onclick="s110SaveSupport()">حفظ الرسالة</button></section></div>`;activate('supportPage');
}
function renderLegal(){
  const p=ensurePage('legalPage');p.innerHTML=`<div class="s110-page" data-s110-page="legal">${top('الخصوصية والشروط','معلومات مختصرة قبل الإطلاق',"showPage('profilePage')")}<section class="s110-assessment"><b>خصوصية الطالب</b><p>يستخدم سهيل بيانات الحساب والإجابات لعرض التقدم وتقييم الأداء. لا تُباع بيانات المستخدمين للمعلنين.</p></section><section class="s110-assessment" style="margin-top:10px"><b>الاستخدام التعليمي</b><p>مؤشر الجاهزية تقييم داخلي مبني على أداء الطالب في التطبيق، وليس نتيجة رسمية أو ضمانًا لدرجة محددة.</p></section></div>`;activate('legalPage');
}
window.s110SaveSupport=function(){const box=document.getElementById('s110SupportText'),v=String(box?.value||'').trim();if(!v){alert('اكتب رسالتك أولًا');return}let rows=[];try{rows=JSON.parse(localStorage.getItem('suhail_feedback')||'[]')}catch(_){}rows.unshift({id:Date.now(),text:v,date:new Date().toISOString(),source:'focus_support'});storageSet('suhail_feedback',JSON.stringify(rows.slice(0,50)));box.value='';alert('تم حفظ رسالتك')};
function navHtml(){const items=[['summaries','الملخصات','summary','summariesPage'],['collections','التجميعات','collection','collectionsPage'],['home','الرئيسية','home','homePage'],['performance','أدائي','performance','statsPage'],['account','الحساب','account','profilePage']];return `<nav class="s110-bottom-nav" id="s110BottomNav" aria-label="القائمة الرئيسية">${items.map(([id,label,ic,page])=>`<button class="s110-nav-btn ${id==='home'?'home':''}" data-s110-nav="${id}" onclick="showPage('${page}')">${icon(ic)}<span>${label}</span></button>`).join('')}</nav>`}
function ensureNav(){let nav=document.getElementById('s110BottomNav');if(!nav){document.querySelector('.screen')?.insertAdjacentHTML('beforeend',navHtml());nav=document.getElementById('s110BottomNav')}return nav}
function syncNav(page){const map={homePage:'home',summariesPage:'summaries',collectionsPage:'collections',statsPage:'performance',nextStepPage:'home',profilePage:'account'};const id=map[page]||'';ensureNav()?.querySelectorAll('[data-s110-nav]').forEach(b=>b.classList.toggle('active',b.dataset.s110Nav===id))}
function route(id){
  if(id==='homePage')return renderHome();if(id==='collectionsPage')return renderCollections();if(id==='statsPage')return renderPerformance();if(id==='nextStepPage')return renderNext();if(id==='profilePage')return renderAccount();if(id==='supportPage')return renderSupport();if(id==='legalPage')return renderLegal();
  if(id==='summariesPage'){syncNav(id);return}
  syncNav(id);document.body.classList.toggle('s110-exam-active',id==='exercisePage');
}
function patchShowPage(){if(window.__s110ShowPatched||typeof window.showPage!=='function')return;window.__s110ShowPatched=true;const old=window.showPage.bind(window);window.showPage=function(id){if(['collectionsPage','nextStepPage','supportPage','legalPage'].includes(id)){route(id);return}const out=old.apply(this,arguments);setTimeout(()=>route(id),15);setTimeout(()=>route(id),180);return out}}
function installObservers(){['homePage','statsPage','profilePage'].forEach(id=>{const p=ensurePage(id);new MutationObserver(()=>{if(rendering||!p.classList.contains('active'))return;clearTimeout(observerTimer);observerTimer=setTimeout(()=>{if(!p.querySelector('[data-s110-page]'))route(id)},60)}).observe(p,{childList:true})})}
window.s110ToggleTheme=function(e){e?.stopPropagation();const dark=isDark();storageSet('s55_theme',dark?'light':'dark');document.body.classList.toggle('s55-dark',!dark);document.documentElement.setAttribute('data-theme',!dark?'dark':'light');renderAccount()};
function install(){if(installed)return;installed=true;document.body.classList.add('s110-focus-ready');ensurePage('collectionsPage');ensurePage('nextStepPage');ensurePage('supportPage');ensurePage('legalPage');ensureNav();patchShowPage();installObservers();
  const active=[...document.querySelectorAll('.page')].find(p=>p.classList.contains('active'))?.id;if(active==='homePage'||!active)renderHome();else route(active);
  window.SuhailFocus110={version:VERSION,renderHome,renderPerformance,renderCollections,renderNext,snapshot};window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,180),{once:true});else setTimeout(install,180);
})();
