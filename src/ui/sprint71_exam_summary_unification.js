/* Suhail Sprint 71 — exam stability and one summary-menu language. */
(function(){
  'use strict';
  const VERSION='72.0.0';
  const BACK='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg>';
  const ICONS={
    summaries:'<svg viewBox="0 0 24 24"><path d="M5 4h12a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2V4Z"/><path d="M9 8h6M9 12h6M9 16h4"/></svg>',
    tahsili:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5"/><path d="m15 9 5-5M17 4h3v3"/></svg>',
    quant:'<svg viewBox="0 0 24 24"><path d="M6 6h12M6 18h12M8 12h8M12 3v18"/></svg>',
    verbal:'<svg viewBox="0 0 24 24"><path d="M6 5h12M9 5c0 7 2 11 6 14M15 5c0 7-2 11-6 14M5 19h14"/></svg>',
    physics:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1.2"/><ellipse cx="12" cy="12" rx="9" ry="4"/><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(35 12 12)"/><ellipse cx="12" cy="12" rx="4" ry="9" transform="rotate(-35 12 12)"/></svg>',
    chemistry:'<svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 18l-5-9V3M8 15h8"/></svg>',
    math:'<svg viewBox="0 0 24 24"><path d="M5 5h14M7 9l3 3-3 3M13 15h5"/></svg>',
    biology:'<svg viewBox="0 0 24 24"><path d="M8 3c5 2 3 7 8 9M16 3c-5 2-3 7-8 9M8 12c5 2 3 7 8 9M16 12c-5 2-3 7-8 9M8 7h8M8 17h8"/></svg>',
    book:'<svg viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z"/><path d="M8 7h7M8 11h6"/></svg>',
    unit:'<svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="7" cy="7" r="1"/><circle cx="7" cy="12" r="1"/><circle cx="7" cy="17" r="1"/></svg>',
    search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/></svg>'
  };
  const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const state={view:'gateway',exam:'',subject:'',stage:'',query:'',emptyTitle:'',emptyIcon:'book'};
  let internalLegacy=false;

  const legacy={
    showPage:typeof window.showPage==='function'?window.showPage.bind(window):null,
    openSubject:typeof window.s59OpenSubject==='function'?window.s59OpenSubject.bind(window):null,
    openUnit:typeof window.s17OpenUnit==='function'?window.s17OpenUnit.bind(window):null,
    courses:typeof window.s17Courses==='function'?window.s17Courses.bind(window):null,
    units:typeof window.s17Units==='function'?window.s17Units.bind(window):null
  };

  function physicsBank(){
    try{return (typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries:[]).filter(x=>String(x.subject||'').trim()==='فيزياء');}
    catch(_){return [];}
  }
  function stageOrder(){
    const preferred=['فيزياء 1','فيزياء 2','فيزياء 3-1','فيزياء 3-2'];
    const found=[...new Set(physicsBank().map(x=>String(x.stage||'فيزياء').trim()).filter(Boolean))];
    return [...preferred.filter(x=>found.includes(x)),...found.filter(x=>!preferred.includes(x))];
  }
  function unitGroups(stage){
    const map=new Map();
    physicsBank().filter(x=>String(x.stage||'').trim()===stage).forEach(x=>{
      const key=String(x.unit||'وحدة غير مصنفة').trim();
      if(!map.has(key))map.set(key,[]);
      map.get(key).push(x);
    });
    return [...map.entries()].map(([unit,items])=>({unit,items}));
  }
  function icon(name){return ICONS[name]||ICONS.book;}
  function activePage(){return document.querySelector('.page.active');}
  function summariesPage(){return document.getElementById('summariesPage');}

  function header(title,subtitle,back){
    return `<header class="s71-header"><button class="s71-back" type="button" onclick="${back}" aria-label="العودة">${BACK}</button><div class="s71-header-copy"><span>الملخصات</span><h1>${esc(title)}</h1>${subtitle?`<p>${esc(subtitle)}</p>`:''}</div></header>`;
  }
  function card({title,subtitle,iconName,badge,action,disabled=false}){
    return `<button class="s71-menu-card${disabled?' is-disabled':''}" type="button" ${disabled?'disabled':`onclick="${action}"`}><span class="s71-menu-icon">${icon(iconName)}</span><span class="s71-menu-copy"><b>${esc(title)}</b><small>${esc(subtitle)}</small>${badge?`<em>${esc(badge)}</em>`:''}</span><span class="s71-menu-arrow">‹</span></button>`;
  }
  function shell(inner){return `<div class="s59-page s71-page">${inner}</div>`;}

  function renderGateway(page){
    const count=physicsBank().length;
    page.innerHTML=shell(`${header('اختر مسارك','',"showPage('homePage')")}<div class="s71-list">${card({title:'تحصيلي',subtitle:'رياضيات، فيزياء، كيمياء، والأحياء وعلم البيئة',iconName:'tahsili',badge:`${count} ملخص منشور`,action:"s71OpenExam('تحصيلي')"})}${card({title:'قدرات كمي',subtitle:'المهارات الحسابية والهندسية والجبر وتحليل البيانات',iconName:'quant',badge:'المحتوى قيد الاعتماد',action:"s71OpenExam('قدرات كمي')"})}${card({title:'قدرات لفظي',subtitle:'التناظر والاستيعاب وإكمال الجمل وبقية المهارات',iconName:'verbal',badge:'المحتوى قيد الاعتماد',action:"s71OpenExam('قدرات لفظي')"})}</div>`);
  }
  function renderTahsili(page){
    const p=physicsBank().length;
    const rows=[
      {title:'فيزياء',subtitle:'الكتب والوحدات والملخصات المعتمدة',iconName:'physics',badge:`${p} ملخص`,action:"s71OpenSubject('فيزياء')"},
      {title:'كيمياء',subtitle:'تظهر الملخصات بعد المراجعة والاعتماد',iconName:'chemistry',badge:'غير منشور',action:"s71OpenEmpty('كيمياء','chemistry')"},
      {title:'رياضيات',subtitle:'تظهر الملخصات بعد المراجعة والاعتماد',iconName:'math',badge:'غير منشور',action:"s71OpenEmpty('رياضيات','math')"},
      {title:'الأحياء وعلم البيئة',subtitle:'تظهر الملخصات بعد المراجعة والاعتماد',iconName:'biology',badge:'غير منشور',action:"s71OpenEmpty('الأحياء وعلم البيئة','biology')"}
    ];
    page.innerHTML=shell(`${header('مواد التحصيلي','اختر المادة التي تريد مراجعتها',"s71OpenGateway()")}<div class="s71-section-label"><b>المواد</b></div><div class="s71-list">${rows.map(card).join('')}</div>`);
  }
  function abilityRows(exam){
    if(exam==='قدرات كمي')return [
      ['مسائل حسابية','النسب، المتوسطات، السرعة، والعمل','quant'],['مسائل هندسية','المساحات والزوايا والأشكال','math'],['مسائل جبرية','المعادلات والأسس والجذور','unit'],['تحليل بيانات وإحصاء','الجداول والرسوم والاحتمالات','book']
    ];
    return [
      ['تناظر لفظي','العلاقة بين كلمتين وما يشبهها','verbal'],['استيعاب مقروء','فهم النص والاستنتاج من الفقرة','book'],['إكمال جمل','اختيار اللفظ المناسب للسياق','unit'],['الخطأ السياقي والارتباط','تمييز الكلمة المختلفة والعلاقة','verbal']
    ];
  }
  function renderAbility(page,exam){
    const rows=abilityRows(exam);
    page.innerHTML=shell(`${header(exam,'اختر المهارة؛ ستظهر الملخصات فور اعتمادها',"s71OpenGateway()")}<div class="s71-list">${rows.map(r=>card({title:r[0],subtitle:r[1],iconName:r[2],badge:'قيد الإعداد',action:`s71OpenEmpty('${esc(r[0])}','${r[2]}','${esc(exam)}')`})).join('')}</div>`);
  }
  function renderStages(page){
    const stages=stageOrder();
    page.innerHTML=shell(`${header('فيزياء','اختر الكتاب المناسب لك',"s71OpenExam('تحصيلي')")}<div class="s71-section-label"><b>كتب الفيزياء</b><span>${physicsBank().length} ملخصًا معتمدًا</span></div><div class="s71-list">${stages.map(stage=>{const units=unitGroups(stage);const lessons=units.reduce((n,u)=>n+u.items.length,0);return card({title:stage,subtitle:`${units.length} وحدات مرتبة`,iconName:'book',badge:`${lessons} درس`,action:`s71OpenStage('${esc(stage)}')`});}).join('')}</div>`);
  }
  function renderUnits(page){
    const all=unitGroups(state.stage);
    const q=String(state.query||'').trim().toLowerCase();
    const rows=q?all.filter(x=>`${x.unit} ${x.items.map(i=>i.title).join(' ')}`.toLowerCase().includes(q)):all;
    page.innerHTML=shell(`${header(state.stage,'اختر الوحدة التي تريد مراجعتها',"s71OpenSubject('فيزياء')")}<label class="s71-search">${icon('search')}<input id="s71UnitSearch" value="${esc(state.query)}" placeholder="ابحث باسم الوحدة أو الدرس" oninput="s71FilterUnits(this.value)" autocomplete="off"><button type="button" onclick="s71FilterUnits('')" aria-label="مسح البحث">×</button></label><div class="s71-section-label"><b>الوحدات</b><span>${rows.length} من ${all.length}</span></div><div class="s71-list">${rows.map((x,i)=>card({title:x.unit,subtitle:(x.items[0]?.simple_idea||x.items[0]?.summary||'ملخصات وتعريفات وقوانين الوحدة').slice(0,105),iconName:'unit',badge:`${x.items.length} دروس`,action:`s71OpenUnit('${esc(state.stage)}','${esc(x.unit)}')`})).join('')}</div>${rows.length?'':'<div class="s71-empty"><b>لا توجد نتيجة مطابقة</b><span>جرّب كلمة أقصر أو امسح البحث.</span></div>'}`);
  }
  function renderEmpty(page){
    const back=state.exam&&state.exam!=='تحصيلي'?`s71OpenExam('${esc(state.exam)}')`:`s71OpenExam('تحصيلي')`;
    page.innerHTML=shell(`${header(state.emptyTitle,'المحتوى يظهر فقط بعد مراجعته واعتماده',back)}<div class="s71-empty s71-empty-large"><span class="s71-empty-icon">${icon(state.emptyIcon)}</span><b>لا توجد ملخصات منشورة هنا حاليًا</b><span>حافظنا على نفس شكل القائمة والتنقل، وسيظهر المحتوى داخلها مباشرة عند اعتماده من لوحة الإدارة.</span></div>`);
  }
  function render(){
    const page=summariesPage();if(!page)return;
    page.className='page active';
    if(state.view==='tahsili')renderTahsili(page);
    else if(state.view==='ability')renderAbility(page,state.exam);
    else if(state.view==='stages')renderStages(page);
    else if(state.view==='units')renderUnits(page);
    else if(state.view==='empty')renderEmpty(page);
    else renderGateway(page);
    document.body.removeAttribute('data-s71-legacy-detail');
    window.SuhailUI70?.update?.();
  }
  function show(){
    const page=summariesPage();if(!page)return;
    if(!page.classList.contains('active')&&legacy.showPage){legacy.showPage('summariesPage');}
    requestAnimationFrame(render);
    setTimeout(()=>{if(activePage()?.id==='summariesPage'&&!internalLegacy)render();},90);
  }

  window.s71OpenGateway=function(){Object.assign(state,{view:'gateway',exam:'',subject:'',stage:'',query:''});internalLegacy=false;show();};
  window.s71OpenExam=function(exam){exam=String(exam||'').trim();Object.assign(state,{view:exam==='تحصيلي'?'tahsili':'ability',exam,subject:'',stage:'',query:''});internalLegacy=false;show();};
  window.s71OpenSubject=function(subject){subject=String(subject||'').trim();if(subject==='فيزياء'){Object.assign(state,{view:'stages',exam:'تحصيلي',subject,stage:'',query:''});}else{Object.assign(state,{view:'empty',exam:'تحصيلي',subject,emptyTitle:subject,emptyIcon:subject==='كيمياء'?'chemistry':subject==='رياضيات'?'math':'biology'});}internalLegacy=false;show();};
  window.s71OpenStage=function(stage){Object.assign(state,{view:'units',exam:'تحصيلي',subject:'فيزياء',stage:String(stage||''),query:''});internalLegacy=false;show();};
  window.s71FilterUnits=function(value){state.query=String(value||'');render();const input=document.getElementById('s71UnitSearch');if(input){input.focus({preventScroll:true});try{input.setSelectionRange(input.value.length,input.value.length);}catch(_){}}};
  window.s71OpenEmpty=function(title,iconName,exam){Object.assign(state,{view:'empty',exam:exam||'تحصيلي',emptyTitle:String(title||''),emptyIcon:iconName||'book'});internalLegacy=false;show();};
  window.s71OpenUnit=function(stage,unit){
    internalLegacy=true;document.body.setAttribute('data-s71-legacy-detail','1');
    try{
      if(typeof window.s17OpenUnitStable==='function'){
        window.s17OpenUnitStable(encodeURIComponent(stage),encodeURIComponent(unit));
      }else if(typeof legacy.openUnit==='function'){
        legacy.openUnit(encodeURIComponent(stage),encodeURIComponent(unit));
      }
      window.SuhailUI70?.update?.();
    }finally{setTimeout(()=>{internalLegacy=false;},40);}
  };

  /* Compatibility: every old entry opens the same hierarchy. */
  window.s59OpenGateway=window.s71OpenGateway;
  window.openSummariesHome=window.s71OpenGateway;
  window.s28SummariesGateway=window.s71OpenGateway;
  window.s59OpenExam=window.s71OpenExam;
  window.openSummaryExam=window.s71OpenExam;
  window.s59OpenSubject=function(subject){window.s71OpenSubject(subject);};
  window.openSummarySubject=function(subject){window.s71OpenSubject(subject);};
  window.openSummaryUnit=function(subject,unit,exam){
    if(String(subject||'')==='فيزياء'){
      const item=physicsBank().find(x=>String(x.unit||'')===String(unit||''));
      if(item)return window.s71OpenUnit(item.stage||'فيزياء 1',unit);
    }
    window.s71OpenEmpty(unit||subject,'book',exam||'تحصيلي');
  };
  window.s17Courses=function(){window.s71OpenSubject('فيزياء');};
  window.s17Units=function(stage){window.s71OpenStage(stage);};

  if(legacy.showPage&&!window.__s71ShowPatched){
    window.__s71ShowPatched=true;
    window.showPage=function(id){
      const result=legacy.showPage.apply(this,arguments);
      if(id==='summariesPage'&&!internalLegacy){Object.assign(state,{view:'gateway',exam:'',subject:'',stage:'',query:''});setTimeout(render,95);}
      return result;
    };
  }

  /* Final exam watchdog: no overlays, no disabled unanswered choices, no stale nav. */
  function stabilizeExam(){
    let active=false;try{active=Array.isArray(activeQuestions)&&activeQuestions.length>0&&!examFinished;}catch(_){ }
    const page=document.getElementById('exercisePage'),quiz=document.getElementById('quizPanel');
    if(!active||!page?.classList.contains('active')||quiz?.classList.contains('hidden'))return;
    document.body.classList.add('s71-exam-active');
    const result=(()=>{try{return questionResults?.[activeIndex]||null}catch(_){return null}})();
    document.querySelectorAll('#choicesBox .choice').forEach(button=>{if(!result?.answered)button.disabled=false;});
    const next=document.getElementById('nextBtn');if(next)next.disabled=!result?.answered;
    document.getElementById('sourcePanel')?.classList.add('hidden');
    window.SuhailFeedback68?.sync?.();
  }
  function patchExam(name){
    const old=window[name];if(typeof old!=='function'||old.__s71)return;
    const fn=function(){
      document.body.classList.remove('s71-exam-active');
      const out=old.apply(this,arguments);
      requestAnimationFrame(stabilizeExam);setTimeout(stabilizeExam,80);
      return out;
    };
    Object.assign(fn,old);fn.__s71=true;window[name]=fn;
  }
  ['beginExamWithMode','loadCurrentQuestion','nextQuiz','prevQuiz'].forEach(patchExam);
  const oldFinish=window.finishExam;
  if(typeof oldFinish==='function'&&!oldFinish.__s71){const fn=function(){document.body.classList.remove('s71-exam-active');return oldFinish.apply(this,arguments)};Object.assign(fn,oldFinish);fn.__s71=true;window.finishExam=fn;}

  function install(){
    setTimeout(()=>{if(activePage()?.id==='summariesPage')window.s71OpenGateway();},120);
    window.SUHAIL_RELEASE=VERSION;
    window.SuhailSprint71={version:VERSION,render,stabilizeExam,state};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
