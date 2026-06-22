/* Suhail Sprint 59 — canonical summaries hierarchy and navigation contract.
   Owns only summaries routing, back-icon normalization and bottom-nav visibility. */
(function(){
  'use strict';

  const VERSION='61.0.0';
  const legacySummaryRender=typeof window.renderSummariesPage==='function' ? window.renderSummariesPage : null;
  const legacyOpenPhysics=typeof window.s28OpenPhysics==='function' ? window.s28OpenPhysics : null;
  const ORDER={
    exams:['تحصيلي','قدرات لفظي','قدرات كمي'],
    tahsili:['فيزياء','كيمياء','رياضيات','الأحياء وعلم البيئة']
  };
  const state={view:'gateway',exam:'',subject:'',unit:'',richPhysics:false};

  function esc(v){return String(v==null?'':v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function norm(v){return String(v||'').normalize('NFKD').replace(/[\u064B-\u065F\u0670]/g,'').replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/ى/g,'ي').replace(/[^\u0600-\u06FFa-zA-Z0-9]+/g,' ').trim().toLowerCase();}
  function allItems(){try{return Array.isArray(summaries)?summaries:[];}catch(_){return [];}}
  function physicsItems(){
    try{
      const bank=(typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries))?smartSummaries:[];
      return bank.filter(x=>String(x.exam||x.track||'تحصيلي').trim()==='تحصيلي'&&String(x.subject||'').trim()==='فيزياء');
    }catch(_){return [];}
  }
  function items(exam,subject){return allItems().filter(x=>String(x.exam||'تحصيلي').trim()===exam&&(!subject||String(x.subject||'').trim()===subject));}
  function exactItem(exam,subject,unit){return items(exam,subject).find(x=>String(x.unit||'').trim()===String(unit||'').trim())||null;}
  function activePage(){return document.querySelector('.page.active');}

  const BACK_SVG='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 5.5 15 12l-6.5 6.5"/></svg>';
  function normalizeBackIcons(root){
    const scope=root&&root.querySelectorAll?root:document;
    scope.querySelectorAll('.s54-back,.s28-back-btn,.s17-hero-btn.back,[aria-label*="العودة"],[aria-label*="رجوع"]').forEach(el=>{
      if(el.closest('.s54-bottom-nav,.s54-lift-nav'))return;
      el.classList.add('s59-unified-back');
      if(el.dataset.s59Back!=='1'){
        el.dataset.s59Back='1';
        el.innerHTML=BACK_SVG;
      }
    });
  }

  function isExamActive(){
    const page=activePage();
    if(!page)return false;
    if(page.id==='exercisePage'){
      try{if(typeof isExamInProgress==='function')return !!isExamInProgress();}catch(_){}
      return !!page.querySelector('#quizCard:not(.hidden) .quiz-question,#choicesBox .choice');
    }
    if(page.id==='s54DiagnosticPage')return !!page.querySelector('.s54-diag-progress+.s54-question,.s54-options');
    return false;
  }

  function navKeyForPage(id){
    if(id==='summariesPage'||id==='skillHubPage')return'summaries';
    if(id==='reviewPage'||id==='errorReviewPage')return'review';
    if(id==='tasksPage'||id==='statsPage')return'tasks';
    if(['profilePage','studentSetupPage','adminSettingsPage','challengePage','questionManagementPage','aiGeneratorPage','savedQuestionsPage'].includes(id))return'profile';
    return'home';
  }

  let syncTimer=null;
  function syncNavigation(){
    clearTimeout(syncTimer);
    syncTimer=setTimeout(()=>{
      const body=document.body;if(!body)return;
      const exam=isExamActive();
      body.classList.toggle('s59-exam-active',exam);
      if(exam){
        body.classList.add('s54-mode-exam');
        body.classList.remove('s54-mode-main','s54-mode-summary','s54-lift-open','s28-nav-open');
      }else{
        body.classList.remove('s54-mode-exam','s54-mode-summary','s54-lift-open','s28-nav-open','s28-branch-page','s28-exam-page');
        body.classList.add('s54-mode-main','s59-nav-visible');
      }
      const page=activePage();
      if(page?.id==='summariesPage'&&!state.richPhysics&&!page.querySelector('.s59-page')){
        requestAnimationFrame(render);
      }
      const key=navKeyForPage(page?.id||'homePage');
      document.querySelectorAll('#s54BottomNav .s54-nav-btn').forEach(btn=>btn.classList.toggle('active',btn.dataset.s54Nav===key));
      normalizeBackIcons(page||document);
    },20);
  }

  function showSummaryPage(){
    const page=document.getElementById('summariesPage');
    if(!page)return;
    if(!page.classList.contains('active')){
      if(typeof window.showPage==='function')window.showPage('summariesPage');
      else if(typeof activatePage==='function')activatePage('summariesPage');
    }
    requestAnimationFrame(()=>{render();syncNavigation();});
  }

  function icon(name){
    const icons={
      tahsili:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="m14 10 6-6M16 4h4v4"/></svg>',
      verbal:'<svg viewBox="0 0 24 24"><path d="M6 5h12M9 5c0 7 2 11 6 14M15 5c0 7-2 11-6 14M5 19h14"/></svg>',
      quant:'<svg viewBox="0 0 24 24"><path d="M6 7h12M6 17h12M8 12h8M12 4v16"/></svg>',
      physics:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1.4"/><ellipse cx="12" cy="12" rx="9" ry="4"/><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(35 12 12)"/><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(-35 12 12)"/></svg>',
      chemistry:'<svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 18l-5-9V3M8 15h8"/></svg>',
      math:'<svg viewBox="0 0 24 24"><path d="M5 5h14M7 9l3 3-3 3M13 15h5"/></svg>',
      biology:'<svg viewBox="0 0 24 24"><path d="M8 3c5 2 3 7 8 9M16 3c-5 2-3 7-8 9M8 12c5 2 3 7 8 9M16 12c-5 2-3 7-8 9M8 7h8M8 17h8"/></svg>',
      book:'<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z"/><path d="M8 7h7M8 11h6"/></svg>',
      search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/></svg>',
      check:'<svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg>',
      law:'<svg viewBox="0 0 24 24"><path d="M6 4h12v16H6zM9 8h6M9 12h6M9 16h4"/></svg>',
      trap:'<svg viewBox="0 0 24 24"><path d="M12 3 2.8 20h18.4Z"/><path d="M12 9v5M12 17h.01"/></svg>'
    };return icons[name]||icons.book;
  }

  function header(title,subtitle,backAction){
    return `<div class="s59-header"><button class="s59-back s59-unified-back" onclick="${backAction}" aria-label="العودة">${BACK_SVG}</button><div class="s59-header-copy"><h1>${esc(title)}</h1>${subtitle?`<p>${esc(subtitle)}</p>`:''}</div><div class="s59-header-mark">${icon('book')}</div></div>`;
  }

  function card(title,subtitle,iconName,badge,action,tone){
    const badgeText=badge===null||badge===undefined?'':(typeof badge==='number'?`${badge} ملخص`:String(badge));
    return `<button class="s59-card ${tone||''}" onclick="${action}"><span class="s59-card-icon">${icon(iconName)}</span><span class="s59-card-copy"><b>${esc(title)}</b><small>${esc(subtitle)}</small>${badgeText?`<em>${esc(badgeText)}</em>`:''}</span><span class="s59-chevron">‹</span></button>`;
  }

  function renderGateway(page){
    const physicsCount=physicsItems().length;
    page.innerHTML=`<div class="s59-page">${header('الملخصات','اختر المسار المناسب',"showPage('homePage')")}<div class="s59-path-grid">
      ${card('تحصيلي','الفيزياء متاحة، وبقية المواد تظهر بعد اعتمادها','tahsili',`${physicsCount} ملخص فيزياء`,"s59OpenExam('تحصيلي')",'tahsili')}
      ${card('قدرات لفظي','لا يوجد محتوى منشور حتى الآن','verbal','غير منشور',"s59OpenExam('قدرات لفظي')",'verbal')}
      ${card('قدرات كمي','لا يوجد محتوى منشور حتى الآن','quant','غير منشور',"s59OpenExam('قدرات كمي')",'quant')}
    </div></div>`;
  }

  function renderTahsili(page){
    const physicsCount=physicsItems().length;
    const rows=[
      ['فيزياء','الكتب والوحدات والقوانين والتعاريف','physics',physicsCount,"s59OpenSubject('فيزياء')"],
      ['كيمياء','سيظهر المحتوى بعد اعتماده من لوحة الأدمن','chemistry','غير منشور',"s59OpenSubject('كيمياء')"],
      ['رياضيات','سيظهر المحتوى بعد اعتماده من لوحة الأدمن','math','غير منشور',"s59OpenSubject('رياضيات')"],
      ['الأحياء وعلم البيئة','سيظهر المحتوى بعد اعتماده من لوحة الأدمن','biology','غير منشور',"s59OpenSubject('الأحياء وعلم البيئة')"]
    ];
    page.innerHTML=`<div class="s59-page">${header('التحصيلي','اختر المادة',"s59OpenGateway()")}
      <div class="s59-section-title"><b>مواد التحصيلي</b><span>${physicsCount} ملخصًا معتمدًا</span></div>
      <div class="s59-path-grid">${rows.map(r=>card(r[0],r[1],r[2],r[3],r[4],'subject')).join('')}</div>
    </div>`;
  }

  function renderUnavailable(page,exam,subject){
    const title=exam==='تحصيلي'?subject:exam;
    const back=exam==='تحصيلي'?"s59OpenExam('تحصيلي')":"s59OpenGateway()";
    page.innerHTML=`<div class="s59-page s59-catalog-page">${header(title,'المحتوى يضاف بعد مراجعته واعتماده',back)}
      <div class="s59-catalog-grid">
        <section class="s59-catalog-empty">
          <span class="s59-catalog-icon">${icon(exam==='قدرات لفظي'?'verbal':exam==='قدرات كمي'?'quant':subject==='كيمياء'?'chemistry':subject==='رياضيات'?'math':'biology')}</span>
          <b>لا توجد ملخصات منشورة هنا حاليًا</b>
          <p>لن يضاف أي محتوى تلقائي. يظهر المحتوى فقط بعد إدخاله ومراجعته واعتماده من لوحة الأدمن.</p>
        </section>
      </div>
    </div>`;
  }

  function renderUnitList(page,exam,subject){
    const list=items(exam,subject);
    const title=exam==='تحصيلي'?subject:exam;
    const subtitle=exam==='تحصيلي'?'اختر الوحدة التي تريد مراجعتها':'اختر المهارة الأساسية التي تريد تثبيتها';
    const back=exam==='تحصيلي'?"s59OpenExam('تحصيلي')":"s59OpenGateway()";
    page.innerHTML=`<div class="s59-page">${header(title,subtitle,back)}<label class="s59-search">${icon('search')}<input id="s59SummarySearch" type="search" placeholder="ابحث باسم الوحدة أو المفهوم…" oninput="s59FilterUnits(this.value)" autocomplete="off"><button type="button" onclick="s59ClearSearch()" aria-label="مسح البحث">×</button></label><div class="s59-search-meta" id="s59SearchMeta">${list.length} وحدة</div><div class="s59-unit-grid" id="s59UnitGrid">${list.map((x,i)=>{
      const hay=norm([x.unit,x.summary,...(x.keywords||[]),...(x.key_points||[])].join(' '));
      const tags=(x.keywords||[]).slice(0,3).map(k=>`<span>${esc(k)}</span>`).join('');
      return `<button class="s59-unit" data-search="${esc(hay)}" onclick="s59OpenUnit('${esc(exam)}','${esc(subject)}','${esc(x.unit)}')"><span class="s59-unit-number">${String(i+1).padStart(2,'0')}</span><span class="s59-unit-copy"><b>${esc(x.unit)}</b><small>${esc(String(x.summary||'').slice(0,115))}${String(x.summary||'').length>115?'…':''}</small><span class="s59-tags">${tags}</span></span><span class="s59-chevron">‹</span></button>`;
    }).join('')}</div><div class="s59-empty hidden" id="s59NoResults">لا توجد نتيجة مطابقة. جرّب كلمة أخرى.</div></div>`;
  }

  function listHtml(values,klass){
    const arr=Array.isArray(values)?values.filter(Boolean):[];
    if(!arr.length)return'<div class="s59-empty-inline">لا يوجد محتوى مضاف بعد.</div>';
    return `<div class="${klass||'s59-list'}">${arr.map(x=>`<div><span>${icon('check')}</span><p>${esc(x)}</p></div>`).join('')}</div>`;
  }

  function renderDetail(page,exam,subject,unit){
    const item=exactItem(exam,subject,unit);
    if(!item){renderUnitList(page,exam,subject);return;}
    const back=`s59OpenSubject('${esc(subject)}','${esc(exam)}')`;
    page.innerHTML=`<div class="s59-page s59-detail">${header(item.unit,`${exam} • ${subject}`,back)}
      <section class="s59-summary-intro"><span>الفكرة الجوهرية</span><p>${esc(item.summary||'')}</p></section>
      <details class="s59-accordion" open><summary><span>${icon('book')}<b>أهم النقاط</b></span><i>⌄</i></summary><div class="s59-accordion-body">${listHtml(item.key_points)}</div></details>
      <details class="s59-accordion"><summary><span>${icon('law')}<b>القوانين والعلاقات</b></span><i>⌄</i></summary><div class="s59-accordion-body">${listHtml(item.laws,'s59-law-list')}</div></details>
      <details class="s59-accordion"><summary><span>${icon('check')}<b>كيف يأتي في الاختبار؟</b></span><i>⌄</i></summary><div class="s59-accordion-body">${listHtml(item.test_ideas)}</div></details>
      <details class="s59-accordion warning"><summary><span>${icon('trap')}<b>لا تخلط والأخطاء الشائعة</b></span><i>⌄</i></summary><div class="s59-accordion-body">${listHtml(item.common_mistakes)}</div></details>
      <button class="s59-related-btn" onclick="s59OpenRelated('${esc(exam)}','${esc(subject)}','${esc(unit)}')"><span>${icon('check')}</span><div><b>الأسئلة المرتبطة</b><small>انتقل إلى الأسئلة المرتبطة بهذه المعلومة</small></div><em>‹</em></button>
    </div>`;
  }

  function relatedItems(exam,subject,unit){
    let bank=[];try{bank=Array.isArray(questions)?questions:[];}catch(_){}
    return bank.filter(q=>{
      try{
        if(typeof getQuestionSummaryRef==='function'){const ref=getQuestionSummaryRef(q);return !!(ref&&ref.exam===exam&&ref.subject===subject&&ref.unit===unit);}
      }catch(_){}
      return String(q.summary_exam||q.exam||'').trim()===exam&&String(q.summary_subject||q.subject||'').trim()===subject&&String(q.summary_unit||q.unit||'').trim()===unit;
    }).slice(0,8);
  }

  function renderRelated(page,exam,subject,unit){
    const rows=relatedItems(exam,subject,unit);
    page.innerHTML=`<div class="s59-page">${header('الأسئلة المرتبطة',`${subject} • ${unit}`,`s59OpenUnit('${esc(exam)}','${esc(subject)}','${esc(unit)}')`)}<div class="s59-related-list">${rows.length?rows.map((q,i)=>`<article class="s59-related-question"><span>سؤال ${i+1}</span><b>${esc(q.question||'')}</b><small>${esc(q.skill||q.category||unit)}</small></article>`).join(''):`<div class="s59-empty"><b>لا توجد أسئلة مرتبطة بهذه المعلومة بعد</b><span>عند إضافة الكلمات المفتاحية المخفية للأسئلة ستظهر هنا تلقائيًا.</span></div>`}</div></div>`;
  }

  function render(){
    if(state.richPhysics&&legacySummaryRender){
      syncNavigation();
      const result=legacySummaryRender();
      setTimeout(()=>{normalizeBackIcons(document.getElementById('summariesPage'));syncNavigation();},30);
      return result;
    }
    const page=document.getElementById('summariesPage');if(!page)return;
    page.className='page active';
    if(state.view==='tahsili')renderTahsili(page);
    else if(state.view==='units')renderUnitList(page,state.exam,state.subject);
    else if(state.view==='detail')renderDetail(page,state.exam,state.subject,state.unit);
    else if(state.view==='related')renderRelated(page,state.exam,state.subject,state.unit);
    else if(state.view==='empty')renderUnavailable(page,state.exam,state.subject);
    else renderGateway(page);
    normalizeBackIcons(page);syncNavigation();
  }

  window.s59OpenGateway=function(){Object.assign(state,{view:'gateway',exam:'',subject:'',unit:'',richPhysics:false});window.__s28Passthrough=false;showSummaryPage();};
  window.s59OpenExam=function(exam){
    exam=String(exam||'').trim();
    if(exam==='تحصيلي'){Object.assign(state,{view:'tahsili',exam,subject:'',unit:'',richPhysics:false});}
    else{const subject=exam==='قدرات لفظي'?'لفظي':'كمي';Object.assign(state,{view:'empty',exam,subject,unit:'',richPhysics:false});}
    window.__s28Passthrough=false;showSummaryPage();
  };
  window.s59OpenSubject=function(subject,forcedExam){
    subject=String(subject||'').trim();
    const exam=forcedExam||(['كمي','لفظي'].includes(subject)?(subject==='كمي'?'قدرات كمي':'قدرات لفظي'):'تحصيلي');
    if(subject==='فيزياء'&&exam==='تحصيلي'&&legacyOpenPhysics){
      Object.assign(state,{view:'physics',exam,subject,unit:'',richPhysics:true});
      window.__s28Passthrough=true;
      legacyOpenPhysics();
      setTimeout(syncNavigation,30);
      return;
    }
    Object.assign(state,{view:'empty',exam,subject,unit:'',richPhysics:false});
    window.__s28Passthrough=false;showSummaryPage();
  };
  window.s59OpenUnit=function(exam,subject,unit){Object.assign(state,{view:'detail',exam,subject,unit,richPhysics:false});window.__s28Passthrough=false;showSummaryPage();};
  window.s59OpenRelated=function(exam,subject,unit){Object.assign(state,{view:'related',exam,subject,unit,richPhysics:false});window.__s28Passthrough=false;showSummaryPage();};
  window.s59FilterUnits=function(value){
    const q=norm(value),cards=[...document.querySelectorAll('#s59UnitGrid .s59-unit')];let visible=0;
    cards.forEach(card=>{const show=q.length<2||String(card.dataset.search||'').includes(q);card.hidden=!show;if(show)visible++;});
    const meta=document.getElementById('s59SearchMeta');if(meta)meta.textContent=q.length<2?`${cards.length} وحدة`:`${visible} نتيجة`;
    document.getElementById('s59NoResults')?.classList.toggle('hidden',visible>0);
  };
  window.s59ClearSearch=function(){const input=document.getElementById('s59SummarySearch');if(input){input.value='';input.focus();}window.s59FilterUnits('');};

  /* Compatibility with every previous entry point. */
  window.s28SummariesGateway=window.s59OpenGateway;
  window.s27SummariesGateway=()=>window.s59OpenExam('تحصيلي');
  window.openSummariesHome=window.s59OpenGateway;
  window.s28OpenSection=function(section){if(section==='tahsili')window.s59OpenExam('تحصيلي');else if(section==='verbal')window.s59OpenExam('قدرات لفظي');else window.s59OpenExam('قدرات كمي');};
  window.openSummaryExam=window.s59OpenExam;
  window.openSummarySubject=function(subject){window.s59OpenSubject(subject);};
  window.openSummaryUnit=function(subject,unit,exam){window.s59OpenUnit(exam||(['كمي','لفظي'].includes(subject)?(subject==='كمي'?'قدرات كمي':'قدرات لفظي'):'تحصيلي'),subject,unit);};
  window.renderSummariesPage=render;

  const previousShow=typeof window.showPage==='function'?window.showPage.bind(window):null;
  if(previousShow&&!window.__s59ShowPatched){
    window.__s59ShowPatched=true;
    window.showPage=function(id){
      const result=previousShow.apply(this,arguments);
      if(id==='summariesPage'&&!state.richPhysics)setTimeout(render,30);
      setTimeout(syncNavigation,45);
      return result;
    };
  }

  const observer=new MutationObserver(()=>syncNavigation());
  if(document.body)observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  document.addEventListener('click',()=>setTimeout(syncNavigation,25),true);
  setInterval(syncNavigation,650);
  setTimeout(()=>{syncNavigation();normalizeBackIcons(document);if(activePage()?.id==='summariesPage')render();},120);
  window.SUHAIL_SUMMARIES_RELEASE=VERSION;
})();
