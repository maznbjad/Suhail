/* Suhail Sprint 55 — final grouped account/settings hub. */
(function(){
  'use strict';
  const VERSION='89.0.0';
  const AVATARS=__S55_AVATARS__;
  const AVATAR_ASSETS=__S55_AVATAR_ASSETS__;
  let legacyShowPage=null;
  let currentView='main';

  function esc(v){return String(v==null?'':v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function parse(raw,fallback){try{return JSON.parse(raw);}catch(_){return fallback;}}
  function session(){try{return typeof getAuthSession==='function'?getAuthSession():null;}catch(_){return null;}}
  function isAdmin(){return session()?.role==='admin';}
  function userId(){const raw=String(session()?.email||'guest').toLowerCase();return raw.replace(/[^a-z0-9]/g,'_')||'guest';}
  function hash(text){let h=2166136261;for(const c of String(text)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;}
  function friendCode(){return `SH-${String(hash(userId())).slice(-6).padStart(6,'0')}`;}
  function normalizeUsername(v){return String(v||'').trim().toLowerCase().replace(/^@+/,'').replace(/[^a-z0-9_]/g,'').slice(0,20);}
  function currentUser(){const s=session()||{};try{const users=typeof getAllUsers==='function'?getAllUsers():[];return users.find(x=>String(x.email||'').toLowerCase()===String(s.email||'').toLowerCase())||s;}catch(_){return s;}}
  function currentUsername(){const s=session()||{},u=currentUser()||{};return normalizeUsername(s.username||u.username||String(s.email||'student').split('@')[0])||'student';}
  function profile(){const s=session()||{};const p=parse(localStorage.getItem(`s54_profile_${userId()}`)||'',{});const studentName=s.name||s.display_name||p.displayName||'طالب سهيل';return {displayName:studentName,username:currentUsername(),gender:p.gender||s.gender||(String(p.avatarId||'').startsWith('female_')?'female':'male'),academicTrack:p.academicTrack||'scientific',examGoals:Array.isArray(p.examGoals)&&p.examGoals.length?p.examGoals:['qudrat','tahsili'],avatarId:p.avatarId||AVATARS.default||'male_02'};}
  function avatarSrc(id){return AVATAR_ASSETS[id]||AVATAR_ASSETS[AVATARS.default]||'';}
  function goalsLabel(gs){const g=Array.isArray(gs)?gs:[];return g.includes('qudrat')&&g.includes('tahsili')?'قدرات وتحصيلي':g.includes('tahsili')?'تحصيلي':'قدرات';}
  function trackLabel(t){return t==='literary'?'أدبي':'علمي';}
  function savedCount(){try{return typeof getHighlights==='function'?getHighlights().length:0;}catch(_){return 0;}}
  function icon(name){const map={
    journey:'<svg viewBox="0 0 24 24"><path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h5M8 16h7"/></svg>',
    target:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="m14 10 6-6M16 4h4v4"/></svg>',
    moon:'<svg viewBox="0 0 24 24"><path d="M20 15.5A8.5 8.5 0 1 1 8.5 4 7 7 0 0 0 20 15.5Z"/><path d="M5 5h2M6 4v2M17 5h2M18 4v2"/></svg>',
    bell:'<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>',
    trophy:'<svg viewBox="0 0 24 24"><path d="M8 4h8v5a4 4 0 0 1-8 0Z"/><path d="M8 6H5v2a3 3 0 0 0 3 3M16 6h3v2a3 3 0 0 1-3 3M12 13v4M8 21h8M9 17h6"/></svg>',
    bookmark:'<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4Z"/></svg>',
    info:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></svg>',
    contact:'<svg viewBox="0 0 24 24"><path d="m3 11 18-8-7 18-3-7Z"/><path d="m11 14 4-4"/></svg>',
    shield:'<svg viewBox="0 0 24 24"><path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6Z"/><path d="m9 12 2 2 4-4"/></svg>',
    terms:'<svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6Z"/><path d="M15 3v4h4M9 11h6M9 15h6M9 19h4"/></svg>',
    faq:'<svg viewBox="0 0 24 24"><path d="M21 12a8.5 8.5 0 0 1-9 8.5L7 22l1.1-3A8.5 8.5 0 1 1 21 12Z"/><path d="M9.8 9a2.3 2.3 0 0 1 4.4 1c0 1.8-2.2 2-2.2 3.5M12 17h.01"/></svg>',
    admin:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 14a2 2 0 0 0 .4 2.2l.1.1-2.2 2.2-.1-.1A2 2 0 0 0 15 18l-.5.2V21h-3v-2.8L11 18a2 2 0 0 0-2.2.4l-.1.1-2.2-2.2.1-.1A2 2 0 0 0 7 14l-.2-.5H4v-3h2.8L7 10a2 2 0 0 0-.4-2.2l-.1-.1 2.2-2.2.1.1A2 2 0 0 0 11 6l.5-.2V3h3v2.8L15 6a2 2 0 0 0 2.2-.4l.1-.1 2.2 2.2-.1.1A2 2 0 0 0 19 10l.2.5H22v3h-2.8Z"/></svg>',
    content:'<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/></svg>',
    arrow:'<svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg>',
    back:'<svg viewBox="0 0 24 24"><path d="m9 5 7 7-7 7"/></svg>'
  };return map[name]||map.info;}
  function isDark(){return localStorage.getItem('s55_theme')==='dark';}
  function applyTheme(){const dark=isDark();document.body.classList.toggle('s55-dark',dark);document.documentElement.setAttribute('data-theme',dark?'dark':'light');}
  function notifyPrefs(){return Object.assign({daily:true,streak:true,reviews:true,challenges:true},parse(localStorage.getItem(`s55_notifications_${userId()}`)||'',{}));}
  function saveNotify(v){localStorage.setItem(`s55_notifications_${userId()}`,JSON.stringify(v));}
  function row(iconName,label,action,value){const valueHtml=value?(String(value).startsWith('@')?`<bdi dir="ltr">${esc(value)}</bdi>`:esc(value)):'';return `<button class="s55-menu-row" onclick="${action}"><span class="s55-row-icon">${icon(iconName)}</span><span class="s55-row-label">${esc(label)}</span><span class="s55-row-value">${valueHtml}</span><span class="s55-row-arrow">${icon('arrow')}</span></button>`;}
  function themeRow(){return `<div class="s55-menu-row"><span class="s55-row-icon">${icon('moon')}</span><span class="s55-row-label">الوضع الداكن</span><button class="s55-switch ${isDark()?'on':''}" onclick="s55ToggleTheme(event)" role="switch" aria-checked="${isDark()}"><i></i></button></div>`;}
  function page(){return document.getElementById('profilePage');}

  function renderMain(){currentView='main';const el=page();if(!el)return;const p=profile();el.innerHTML=`<div class="s55-account-page" data-s55-account="main">
    <h1 class="s55-account-title">الحساب</h1>
    <section class="s55-profile-strip"><div class="s55-avatar"><img src="${avatarSrc(p.avatarId)}" alt="${esc(p.displayName)}"></div><div class="s55-profile-copy"><b>${esc(p.displayName)}</b><span class="s89-username"><bdi dir="ltr">&#64;${esc(p.username)}</bdi></span><span>${goalsLabel(p.examGoals)}${p.examGoals.includes('qudrat')?` • ${trackLabel(p.academicTrack)} للقدرات`:''}</span></div></section>
    <div class="s89-account-group-title">الحساب والنشاط</div>
    <div class="s55-menu-card s89-account-activity">
      ${row('journey','رحلتي التعليمية',"showPage('studentSetupPage')")}
      ${row('target','تحديد المستوى',"showPage('diagnosticChoicePage')")}
      ${themeRow()}
      ${row('bell','الإشعارات',"s55OpenInfo('notifications')")}
      ${row('trophy','الأصدقاء والتحديات',"showPage('challengePage')",`@${p.username}`)}
      ${row('bookmark','الأسئلة المحفوظة',"showPage('savedQuestionsPage')",savedCount()?`${savedCount()} محفوظة`:'')}
    </div>
    <div class="s89-account-group-title s89-about-title">عن سهيل</div>
    <div class="s55-menu-card s89-about-card">
      ${row('info','عن سهيل',"s55OpenInfo('about')")}
      ${row('contact','تواصل معنا',"s55OpenInfo('contact')")}
      ${row('shield','سياسة الخصوصية',"s55OpenInfo('privacy')")}
      ${row('terms','الشروط والأحكام',"s55OpenInfo('terms')")}
      ${row('faq','الأسئلة الشائعة',"s55OpenInfo('faq')")}
    </div>
    ${isAdmin()?`<div class="s55-admin-label">إدارة سهيل</div><div class="s55-admin-card">${row('admin','لوحة إعدادات الأدمن',"showPage('adminSettingsPage')")}${row('content','إدارة المحتوى',"showPage('questionManagementPage')")}</div>`:''}
    <div class="s55-version"><b>V.1.0.89</b><span>2026 سهيل</span></div>
    <div class="s55-company"><b>سهيل — تعلم بذكاء</b><span>تطبيق تعليمي للقدرات والتحصيلي<br>جميع الحقوق محفوظة</span></div>
    <button class="s55-logout" onclick="logoutUser()">تسجيل الخروج</button>
  </div>`;applyTheme();requestAnimationFrame(()=>{document.querySelector('#s54BottomNav [data-s54-nav="profile"]')?.classList.add('active');window.SuhailExamPlan88?.renderAccount?.();});}


  const text={
    about:{title:'عن سهيل',body:`<h2>سهيل يختصر لك الطريق</h2><p>سهيل رفيق تعليمي للقدرات والتحصيلي. يجمع الملخصات الذكية، التدريب، مراجعة الأخطاء، قياس الجاهزية، الخطة اليومية، والتحديات مع الأصدقاء في رحلة واحدة واضحة.</p><ul><li>القدرات لها قياس مستقل ويتغير نموذجها بحسب المسار العلمي أو الأدبي.</li><li>التحصيلي له قياس مستقل موحد ولا يتأثر بمسار القدرات.</li><li>مؤشر الجاهزية إرشادي ويتحدث مع تقدم الطالب.</li></ul>`},
    privacy:{title:'سياسة الخصوصية',body:`<h2>خصوصية الطالب أولًا</h2><p>يستخدم سهيل بيانات الحساب والتقدم والإجابات لتخصيص الخطة التعليمية، حفظ الإنجاز، وإظهار مؤشرات الأداء. لا ينبغي مشاركة بيانات الطالب مع جهات إعلانية أو بيعها.</p><ul><li>يجب جمع أقل قدر لازم من البيانات.</li><li>يحق للمستخدم طلب حذف حسابه وبياناته.</li><li>يجب تشفير بيانات الحساب والاتصال بالخادم في نسخة الإنتاج.</li></ul><div class="s55-info-note">هذه صياغة داخلية أولية للتصميم وليست سياسة قانونية نهائية. يجب اعتماد النص القانوني قبل النشر في App Store.</div>`},
    terms:{title:'الشروط والأحكام',body:`<h2>استخدام سهيل</h2><p>سهيل أداة تعليمية مساندة ولا يضمن درجة رسمية بعينها. مؤشر الجاهزية تقدير مبني على أداء الطالب داخل التطبيق، وليس نتيجة صادرة عن جهة الاختبار.</p><ul><li>يمنع نسخ المحتوى أو إعادة نشره دون إذن.</li><li>يجب استخدام الحساب من صاحبه فقط.</li><li>قد تتغير المزايا والمحتوى أثناء التطوير.</li></ul><div class="s55-info-note">يلزم اعتماد نسخة قانونية نهائية وربطها ببيانات المنشأة قبل الإطلاق العام.</div>`}
  };
  function infoHeader(title){return `<div class="s55-info-header"><button class="s55-info-back" onclick="s55BackAccount()" aria-label="العودة">${icon('back')}</button><h1>${esc(title)}</h1><span class="s55-info-spacer"></span></div>`;}
  function renderInfo(kind){currentView=kind;const el=page();if(!el)return;if(kind==='notifications')return renderNotifications();if(kind==='contact')return renderContact();if(kind==='faq')return renderFaq();const item=text[kind]||text.about;el.innerHTML=`<div class="s55-account-page">${infoHeader(item.title)}<div class="s55-info-card">${item.body}</div></div>`;applyTheme();}
  function renderNotifications(){const p=notifyPrefs();const togg=(k,title,sub)=>`<div class="s55-notify-row"><div><b>${title}</b><span>${sub}</span></div><button class="s55-switch ${p[k]?'on':''}" onclick="s55ToggleNotify('${k}')" role="switch" aria-checked="${p[k]}"><i></i></button></div>`;page().innerHTML=`<div class="s55-account-page">${infoHeader('الإشعارات')}<div class="s55-notify-list">${togg('daily','خطة اليوم','تذكير بالجلسة اليومية')}${togg('streak','إنقاذ الستريك','تنبيه قبل انقطاع الأيام المتتالية')}${togg('reviews','المراجعات المستحقة','الأخطاء والقوانين التي حان وقتها')}${togg('challenges','دعوات التحدي','عند وصول تحدٍ من صديق')}</div><div class="s55-info-note">الإشعارات بعد إغلاق التطبيق ستعمل عند ربط نسخة Expo بخدمة APNs.</div></div>`;applyTheme();}
  function renderContact(){page().innerHTML=`<div class="s55-account-page">${infoHeader('تواصل معنا')}<div class="s55-info-card"><h2>وصل ملاحظتك لفريق سهيل</h2><p>اكتب اقتراحًا، بلاغًا عن خطأ، أو فكرة تطوير. تحفظ الرسالة محليًا في النسخة الحالية إلى أن يتم ربط مركز الدعم بالخادم.</p><textarea id="s55ContactText" class="s55-contact-text" placeholder="اكتب رسالتك هنا..."></textarea><button class="s55-send" onclick="s55SubmitSupport()">حفظ الرسالة</button></div></div>`;applyTheme();}
  function renderFaq(){const items=[['هل أقدر أستعد للقدرات والتحصيلي معًا؟','نعم. يحفظ سهيل المسارين داخل الحساب، ولكل واحد تحديد مستوى ونتيجة مستقلة.'],['وش الفرق بين علمي وأدبي؟','هذا الاختيار يخص القدرات فقط ويغير توزيع أسئلة تحديد مستوى القدرات. التحصيلي لا يتغير به.'],['هل مؤشر الجاهزية هو درجتي الرسمية؟','لا. هو مؤشر إرشادي يتحدث مع نتائجك وسرعتك وثبات أدائك داخل سهيل.'],['كيف أحافظ على الستريك؟','نفّذ نشاطًا تعليميًا كل يوم. في آخر 6 ساعات تظهر الساعة الرملية لتنبيهك قبل انقطاع السلسلة.']];page().innerHTML=`<div class="s55-account-page">${infoHeader('الأسئلة الشائعة')}<div class="s55-faq">${items.map(([q,a])=>`<details><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join('')}</div></div>`;applyTheme();}

  window.s55OpenInfo=function(kind){renderInfo(kind);};
  window.s55BackAccount=function(){renderMain();};
  window.s55ToggleTheme=function(event){event?.stopPropagation();localStorage.setItem('s55_theme',isDark()?'light':'dark');applyTheme();if(currentView==='main')renderMain();else renderInfo(currentView);};
  window.s55ToggleNotify=function(k){const p=notifyPrefs();p[k]=!p[k];saveNotify(p);renderNotifications();};
  window.s55SubmitSupport=function(){const box=document.getElementById('s55ContactText');const value=box?.value.trim();if(!value){alert('اكتب رسالتك أولًا');return;}const items=parse(localStorage.getItem('suhail_feedback')||'[]',[]);items.unshift({id:Date.now(),text:value,date:new Date().toLocaleDateString('ar-SA'),source:'account_support'});localStorage.setItem('suhail_feedback',JSON.stringify(items));box.value='';alert('تم حفظ رسالتك');};

  function patchShowPage(){if(window.__s55ShowPatched||typeof window.showPage!=='function')return;window.__s55ShowPatched=true;legacyShowPage=window.showPage.bind(window);window.showPage=function(id){if(id==='profilePage'){currentView='main';const result=legacyShowPage(id);setTimeout(renderMain,125);return result;}return legacyShowPage(id);};}
  function install(){if(window.SUHAIL_FOCUS_MODE)return;applyTheme();patchShowPage();if(document.getElementById('profilePage')?.classList.contains('active'))setTimeout(renderMain,140);window.SUHAIL_RELEASE=VERSION;}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,80));else setTimeout(install,80);
})();
