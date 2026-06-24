/* Suhail Sprint 88 — exam dates and adaptive variable-load study plan. */
(function(){
  'use strict';
  const VERSION='88.0.0';
  const DAY=86400000;
  const BANKS={qudrat:3000,tahsili:2400};
  const BASE_LOAD={light:38,balanced:55,intensive:72};
  const LOAD_LABEL={light:'خفيف',balanced:'متوازن',intensive:'مكثف'};
  const CYCLE=[0.78,1.00,1.16,0.88,1.22,0.66,1.06];
  let installed=false;

  const parse=(raw,fallback)=>{try{return JSON.parse(raw);}catch(_){return fallback;}};
  const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
  const round5=v=>Math.max(0,Math.round(Number(v||0)/5)*5);
  const session=()=>{try{return typeof getAuthSession==='function'?getAuthSession():parse(localStorage.getItem('suhail_auth_user')||'null',null);}catch(_){return null;}};
  const userId=()=>String(session()?.email||'guest').toLowerCase().replace(/[^a-z0-9]/g,'_')||'guest';
  const settingsKey=()=>`s88_exam_plan_settings_${userId()}`;
  const planKey=()=>`s88_exam_plan_${userId()}`;
  const completionKey=()=>`s88_exam_plan_done_${userId()}`;
  const localISO=(d=new Date())=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const dateFrom=s=>{const [y,m,d]=String(s||'').split('-').map(Number);return y&&m&&d?new Date(y,m-1,d):null;};
  const addDays=(s,n)=>{const d=dateFrom(s);if(!d)return'';d.setDate(d.getDate()+n);return localISO(d);};
  const diffDays=(a,b)=>{const da=dateFrom(a),db=dateFrom(b);return da&&db?Math.round((db-da)/DAY):0;};
  const formatDate=s=>{const d=dateFrom(s);return d?new Intl.DateTimeFormat('ar-SA',{weekday:'short',day:'numeric',month:'short'}).format(d):'—';};
  const formatLongDate=s=>{const d=dateFrom(s);return d?new Intl.DateTimeFormat('ar-SA',{day:'numeric',month:'long',year:'numeric'}).format(d):'لم يحدد';};
  const today=()=>localISO(new Date());

  function defaults(){return {qudratDate:'',tahsiliDate:'',intensity:'balanced',updatedAt:0};}
  function settings(){return Object.assign(defaults(),parse(localStorage.getItem(settingsKey())||'',{}));}
  function saveSettings(next){const clean=Object.assign(defaults(),next||{});clean.intensity=BASE_LOAD[clean.intensity]?clean.intensity:'balanced';clean.updatedAt=Date.now();localStorage.setItem(settingsKey(),JSON.stringify(clean));return clean;}
  function history(){try{return typeof getExamHistory==='function'?getExamHistory():parse(localStorage.getItem(`suhail_exam_history_${userId()}`)||'[]',[]);}catch(_){return[];}}
  function diagnostics(){return parse(localStorage.getItem(`s54_diagnostics_${userId()}`)||'',{});}

  function recordsFor(path){return history().filter(r=>path==='qudrat'?String(r.exam||'').includes('قدرات'):String(r.exam||'')==='تحصيلي');}
  function weightedAccuracy(rows,diag){
    let total=0,correct=0;
    rows.slice(0,12).forEach(r=>{const t=Number(r.total||0),c=Number(r.correct||0);total+=t;correct+=c;});
    if(total)return clamp(correct/total,.2,.98);
    const pct=Number(diag?.weightedPercent||diag?.percent||0);
    return pct?clamp(pct/100,.2,.98):.58;
  }
  function weakestQudrat(){
    const rows=history(),sum={quant:{t:0,c:0},verbal:{t:0,c:0}};
    rows.forEach(r=>{const k=String(r.exam||'').includes('لفظي')?'verbal':String(r.exam||'').includes('كمي')?'quant':'';if(!k)return;sum[k].t+=Number(r.total||0);sum[k].c+=Number(r.correct||0);});
    const qa=sum.quant.t?sum.quant.c/sum.quant.t:.58,va=sum.verbal.t?sum.verbal.c/sum.verbal.t:.58;
    return {quant:qa,verbal:va,label:qa<=va?'الكمي':'اللفظي'};
  }
  function weakestTahsili(){
    const map={};
    recordsFor('tahsili').forEach(r=>(r.sections||[]).forEach(s=>{const n=String(s.name||'').trim();if(!n)return;map[n]??={t:0,c:0};map[n].t+=Number(s.total||0);map[n].c+=Number(s.correct||0);}));
    const rows=Object.entries(map).map(([name,v])=>({name,acc:v.t?v.c/v.t:1})).sort((a,b)=>a.acc-b.acc);
    return rows[0]?.name||'المادة الأضعف';
  }
  function examStats(path,date){
    const rows=recordsFor(path),diag=diagnostics()[path],accuracy=weightedAccuracy(rows,diag);
    const attempted=Math.min(BANKS[path],rows.reduce((a,r)=>a+Number(r.total||0),0));
    const days=Math.max(0,diffDays(today(),date));
    const coverage=clamp(.38+(Math.min(days,90)/90)*.42+Math.max(0,.72-accuracy)*.24,.38,.92);
    const target=round5(BANKS[path]*coverage);
    const effectiveSolved=Math.min(BANKS[path],Math.round(attempted*.86));
    const desired=Math.max(0,target-effectiveSolved);
    return {path,date,days,bank:BANKS[path],accuracy,attempted,effectiveSolved,target,desired,remaining:desired,planned:0,weak:path==='qudrat'?weakestQudrat().label:weakestTahsili()};
  }
  function taper(daysLeft){if(daysLeft<=1)return .28;if(daysLeft===2)return .48;if(daysLeft===3)return .66;if(daysLeft<=7)return .88;return 1;}
  function stage(daysLeft,cycle,accuracy,index){
    if(daysLeft<=1)return {id:'calm',label:'تهيئة هادئة',reason:'مراجعة خفيفة دون ضغط قبل الاختبار'};
    if(daysLeft<=3)return {id:'final',label:'مراجعة نهائية',reason:'أخطاء وقوانين ونقاط سريعة فقط'};
    if(daysLeft<=10||cycle===6)return {id:'mock',label:'محاكاة ومراجعة',reason:'تدريب زمني ثم تحليل الأخطاء'};
    if(cycle===5)return {id:'review',label:'يوم خفيف',reason:'تثبيت الأخطاء وإراحة الذهن'};
    if(index<2||accuracy<.58)return {id:'foundation',label:'تأسيس موجه',reason:'فهم الفكرة قبل زيادة سرعة الحل'};
    if(cycle===2||cycle===4)return {id:'push',label:'تدريب مركز',reason:'حمل أعلى لأن اليوم مخصص للتطبيق'};
    return {id:'practice',label:'تدريب متوازن',reason:'مزج بين التدريب والمراجعة'};
  }
  function allocateCount(total,weight){return round5(total*weight);}
  function itemDetail(exam,count,mode){
    if(exam.path==='qudrat'){
      const weak=weakestQudrat(),qWeight=weak.quant <= weak.verbal ? 0.60 : 0.40;
      let quant=round5(count*qWeight);quant=clamp(quant,0,count);const verbal=Math.max(0,count-quant);
      if(mode.id==='calm')return `${Math.max(5,quant)} كمي + ${Math.max(5,verbal)} لفظي • مراجعة سهلة`;
      if(mode.id==='review'||mode.id==='final')return `${count} سؤالًا من الأخطاء السابقة • التركيز على ${weak.label}`;
      if(mode.id==='mock')return `${quant} كمي + ${verbal} لفظي بزمن محدد`;
      return `${quant} كمي + ${verbal} لفظي • الأولوية لـ${weak.label}`;
    }
    if(mode.id==='review'||mode.id==='final')return `${count} سؤالًا من الأخطاء والقوانين • تركيز: ${exam.weak}`;
    if(mode.id==='mock')return `${count} سؤالًا تحصيليًا مختلطًا بزمن محدد`;
    if(mode.id==='foundation')return `${count} سؤالًا بعد مراجعة ملخص قصير • تركيز: ${exam.weak}`;
    return `${count} سؤالًا تحصيليًا مختلطًا • تركيز: ${exam.weak}`;
  }
  function redistribute(capacity,active,alloc,caps){
    let used=Object.values(alloc).reduce((a,b)=>a+b,0),left=capacity-used,guard=0;
    while(left>=5&&guard++<100){
      const candidates=active.filter(e=>{const current=alloc[e.path]||0,max=Number(caps[e.path]||capacity);return e.remaining-current>=5&&current+5<=max;}).sort((a,b)=>(b.remaining/Math.max(1,b.daysLeft))-(a.remaining/Math.max(1,a.daysLeft)));
      if(!candidates.length)break;
      for(const e of candidates){if(left<5)break;const max=Number(caps[e.path]||capacity);if((alloc[e.path]||0)+5>max)continue;alloc[e.path]=(alloc[e.path]||0)+5;left-=5;}
    }
    return alloc;
  }
  function buildPlan(input=settings()){
    const s=Object.assign(defaults(),input||{}),start=today();
    const exams=[];
    if(s.qudratDate&&diffDays(start,s.qudratDate)>=0)exams.push(examStats('qudrat',s.qudratDate));
    if(s.tahsiliDate&&diffDays(start,s.tahsiliDate)>=0)exams.push(examStats('tahsili',s.tahsiliDate));
    const maxDays=Math.max(0,...exams.map(e=>e.days));
    const base=BASE_LOAD[s.intensity]||BASE_LOAD.balanced,days=[];
    for(let i=0;i<maxDays;i++){
      const date=addDays(start,i),active=exams.filter(e=>date<e.date&&e.remaining>0).map(e=>({...e,daysLeft:diffDays(date,e.date)}));
      if(!active.length)continue;
      const cycleFactor=CYCLE[i%7];
      let capacity=round5(base*cycleFactor);
      const ramp=i===0?.84:i===1?.94:1;
      capacity=round5(capacity*ramp);
      const averageCycle=CYCLE.reduce((a,b)=>a+b,0)/CYCLE.length;
      const requiredRate=active.reduce((sum,e)=>sum+(e.remaining/Math.max(1,e.daysLeft)),0);
      let dailyTarget=round5(requiredRate*(cycleFactor/averageCycle)*ramp);
      dailyTarget=Math.min(capacity,Math.max(active.length*5,dailyTarget));
      const scores={};let scoreTotal=0;
      active.forEach(e=>{const rate=e.remaining/Math.max(1,e.daysLeft),urgency=1+Math.min(1.15,14/Math.max(2,e.daysLeft)),need=1+Math.max(0,.68-e.accuracy)*.75;const score=rate*urgency*need*taper(e.daysLeft);scores[e.path]=score;scoreTotal+=score;});
      const alloc={},caps={};
      active.forEach(e=>{let n=scoreTotal?allocateCount(dailyTarget,scores[e.path]/scoreTotal):0;const examCap=round5(dailyTarget*(e.daysLeft<=1?.30:e.daysLeft===2?.48:e.daysLeft===3?.68:1));caps[e.path]=Math.max(5,examCap);n=Math.min(n,caps[e.path],e.remaining);if(n>0&&n<5)n=5;alloc[e.path]=round5(n);});
      redistribute(dailyTarget,active,alloc,caps);
      const items=[];
      active.forEach(a=>{const original=exams.find(e=>e.path===a.path),count=Math.min(original.remaining,alloc[a.path]||0);if(!count)return;const mode=stage(a.daysLeft,i%7,a.accuracy,i);original.remaining-=count;original.planned+=count;items.push({id:`${date}-${a.path}`,path:a.path,exam:a.path==='qudrat'?'القدرات':'التحصيلي',count,mode:mode.id,modeLabel:mode.label,reason:mode.reason,daysLeft:a.daysLeft,detail:itemDetail(a,count,mode),weak:a.weak});});
      const total=items.reduce((a,x)=>a+x.count,0);if(total)days.push({date,index:i,total,items,label:formatDate(date)});
    }
    const result={version:1,generatedAt:Date.now(),today:start,settings:s,exams:Object.fromEntries(exams.map(e=>[e.path,{...e,remainingDesired:e.remaining}])),days};
    localStorage.setItem(planKey(),JSON.stringify(result));return result;
  }
  function loadPlan(force=false){const s=settings(),stored=parse(localStorage.getItem(planKey())||'',null);if(force||!stored||stored.today!==today()||JSON.stringify(stored.settings)!==JSON.stringify(s))return buildPlan(s);return stored;}
  function daysText(n){if(n<0)return'انتهى الموعد';if(n===0)return'اليوم';if(n===1)return'متبقي يوم واحد';if(n===2)return'متبقي يومان';if(n<=10)return`متبقي ${n} أيام`;return`متبقي ${n} يومًا`;}
  function examMeta(path,date,plan){
    if(!date)return {days:'حدد الموعد',sub:'سيبني سهيل الخطة بمجرد حفظ التاريخ',cls:'empty'};
    const n=diffDays(today(),date),e=plan.exams?.[path];
    if(n<0)return {days:'انتهى الموعد',sub:formatLongDate(date),cls:'past'};
    const tight=e&&e.desired>0&&e.planned<e.desired*.82?' • تركيز على الأولويات لضيق المدة':'';return {days:daysText(n),sub:e?`${formatLongDate(date)} • ${e.planned} سؤالًا موزعة${tight}`:`${formatLongDate(date)}`,cls:n<=7?'near':''};
  }
  function icon(name){const map={calendar:'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',plan:'<svg viewBox="0 0 24 24"><path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h5M8 16h7"/></svg>',arrow:'<svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg>',target:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/></svg>'};return map[name]||map.plan;}

  function accountMarkup(){
    const s=settings(),p=loadPlan(),qm=examMeta('qudrat',s.qudratDate,p),tm=examMeta('tahsili',s.tahsiliDate,p),next=p.days?.[0];
    return `<section class="s88-account-planner" id="s88AccountPlanner"><div class="s88-planner-head"><span class="s88-planner-icon">${icon('calendar')}</span><div><b>مواعيد الاختبارات</b><small>سهيل يوزع الجهد حسب الوقت المتبقي ومستواك</small></div></div>
      <label class="s88-date-row ${qm.cls}"><div><b>تاريخ اختبار القدرات القادم</b><span id="s88QudratMeta">${esc(qm.days)} • ${esc(qm.sub)}</span></div><input id="s88QudratDate" type="date" min="${today()}" value="${esc(s.qudratDate)}" aria-label="تاريخ اختبار القدرات"></label>
      <label class="s88-date-row ${tm.cls}"><div><b>تاريخ اختبار التحصيلي القادم</b><span id="s88TahsiliMeta">${esc(tm.days)} • ${esc(tm.sub)}</span></div><input id="s88TahsiliDate" type="date" min="${today()}" value="${esc(s.tahsiliDate)}" aria-label="تاريخ اختبار التحصيلي"></label>
      <div class="s88-load-row"><div><b>إيقاع الخطة</b><span>يتغير العدد يوميًا، وليس حصة ثابتة</span></div><div class="s88-segment">${['light','balanced','intensive'].map(k=>`<button type="button" data-s88-load="${k}" class="${s.intensity===k?'active':''}">${LOAD_LABEL[k]}</button>`).join('')}</div></div>
      <div class="s88-plan-preview"><div><b>${next?`اليوم: ${next.total} سؤالًا`:'حدد موعدًا لبناء الخطة'}</b><span>${next?next.items.map(x=>`${x.exam} ${x.count}`).join(' • '):'ستظهر الأيام الخفيفة والمكثفة والمحاكاة تلقائيًا'}</span></div><button type="button" id="s88OpenPlan">عرض الخطة ${icon('arrow')}</button></div>
    </section>`;
  }
  function bindAccount(){
    const root=document.getElementById('s88AccountPlanner');if(!root)return;
    const update=()=>{const s=settings();s.qudratDate=document.getElementById('s88QudratDate')?.value||'';s.tahsiliDate=document.getElementById('s88TahsiliDate')?.value||'';saveSettings(s);loadPlan(true);renderAccount();patchTasks();};
    root.querySelector('#s88QudratDate')?.addEventListener('change',update);root.querySelector('#s88TahsiliDate')?.addEventListener('change',update);
    root.querySelectorAll('[data-s88-load]').forEach(btn=>btn.addEventListener('click',()=>{const s=settings();s.intensity=btn.dataset.s88Load;saveSettings(s);loadPlan(true);renderAccount();patchTasks();}));
    root.querySelector('#s88OpenPlan')?.addEventListener('click',openPlan);
  }
  function renderAccount(){
    const page=document.getElementById('profilePage'),host=page?.querySelector('.s55-account-page');if(!host)return false;
    const old=host.querySelector('#s88AccountPlanner');if(old)old.remove();
    const profile=host.querySelector('.s55-profile-strip');if(!profile)return false;
    profile.insertAdjacentHTML('afterend',accountMarkup());bindAccount();return true;
  }

  function doneState(){return parse(localStorage.getItem(completionKey())||'',{});}
  function saveDone(v){localStorage.setItem(completionKey(),JSON.stringify(v));}
  function todayDay(plan=loadPlan()){return plan.days?.find(d=>d.date===today())||null;}
  function taskAction(path){return path==='tahsili'?"openExamSetup('تحصيلي')":"openExamSetup('قدرات كمي')";}
  function taskMarkup(item,done){return `<div class="s88-today-item ${done?'done':''}" data-s88-item="${item.id}"><button class="s88-check" type="button" aria-label="تم">${done?'✓':''}</button><button class="s88-task-body" type="button" data-s88-start="${item.path}"><span class="s88-task-count">${item.count}</span><span><b>${esc(item.exam)} — ${esc(item.modeLabel)}</b><small>${esc(item.detail)}</small></span><em>‹</em></button></div>`;}
  function patchTasks(){
    const page=document.getElementById('tasksPage');if(!page||!page.classList.contains('active'))return;
    const shell=page.querySelector('.s39-page')||page,hero=shell.querySelector('.s39-plan-hero');if(!hero)return;
    shell.querySelector('.s88-today-plan')?.remove();const plan=loadPlan(),day=todayDay(plan),done=doneState();
    const html=day?`<section class="s88-today-plan"><div class="s88-today-head"><div><b>خطة موعد الاختبار</b><span>${esc(day.label)} • ${day.total} سؤالًا بتوزيع متغير</span></div><button type="button" data-s88-full>${icon('plan')} الخطة</button></div><div class="s88-today-list">${day.items.map(x=>taskMarkup(x,!!done[x.id])).join('')}</div></section>`:`<section class="s88-today-plan empty"><div class="s88-today-head"><div><b>خطة موعد الاختبار</b><span>حدد تاريخ القدرات أو التحصيلي من الحساب</span></div><button type="button" data-s88-account>إضافة الموعد</button></div></section>`;
    hero.insertAdjacentHTML('afterend',html);
    shell.querySelector('[data-s88-full]')?.addEventListener('click',openPlan);shell.querySelector('[data-s88-account]')?.addEventListener('click',()=>showPage('profilePage'));
    shell.querySelectorAll('.s88-check').forEach(btn=>btn.addEventListener('click',()=>toggleDone(btn.closest('[data-s88-item]')?.dataset.s88Item)));
    shell.querySelectorAll('[data-s88-start]').forEach(btn=>btn.addEventListener('click',()=>{const p=btn.dataset.s88Start;try{if(p==='tahsili')openExamSetup('تحصيلي');else openExamSetup(weakestQudrat().label==='الكمي'?'قدرات كمي':'قدرات لفظي');}catch(_){}}));
  }
  function toggleDone(id){if(!id)return;const d=doneState();d[id]=!d[id];saveDone(d);patchTasks();const day=todayDay(),all=day?.items?.length&&day.items.every(x=>d[x.id]);if(all){try{window.SuhailMotivation87?.recordActivity('exam-plan');window.SuhailMotivation87?.showReaction('celebrate','أنجزت حصة اليوم حسب موعد اختبارك. ممتاز، لا تحتاج لزيادة الحمل.',{title:'خطة اليوم مكتملة 🎉',celebrate:true});}catch(_){}}}

  function ensureOverlay(){let o=document.getElementById('s88PlanOverlay');if(o)return o;o=document.createElement('div');o.id='s88PlanOverlay';o.className='s88-overlay';(document.querySelector('.screen')||document.body).appendChild(o);o.addEventListener('click',e=>{if(e.target===o)closePlan();});return o;}
  function openPlan(){
    const p=loadPlan(),o=ensureOverlay(),s=settings();
    const examSummary=['qudrat','tahsili'].map(path=>{const e=p.exams?.[path],date=s[path+'Date'];if(!date)return'';return `<div class="s88-summary-box"><b>${path==='qudrat'?'القدرات':'التحصيلي'}</b><strong>${e?.planned||0}</strong><span>سؤالًا مخططًا • ${daysText(diffDays(today(),date))}</span></div>`;}).join('');
    const timeline=p.days?.length?p.days.map((d,i)=>`<article class="s88-day-card ${d.date===today()?'today':''}"><div class="s88-day-date"><b>${i===0?'اليوم':esc(d.label)}</b><span>${d.total} سؤالًا</span></div><div class="s88-day-items">${d.items.map(x=>`<div><span class="s88-path ${x.path}">${esc(x.exam)}</span><b>${x.count} سؤالًا — ${esc(x.modeLabel)}</b><small>${esc(x.detail)}</small><em>${esc(x.reason)}</em></div>`).join('')}</div></article>`).join(''):'<div class="s88-empty-plan">حدد موعد اختبار واحد على الأقل من صفحة الحساب.</div>';
    o.innerHTML=`<section class="s88-sheet" role="dialog" aria-modal="true"><header><div><b>الخطة الذكية للاختبارات</b><span>توزيع متغير حسب الأيام المتبقية، الأداء، والمراجعات</span></div><button type="button" data-s88-close>×</button></header><div class="s88-summary-grid">${examSummary||'<div class="s88-empty-plan">لا توجد مواعيد محفوظة</div>'}</div><div class="s88-method"><b>كيف يحسب سهيل الخطة؟</b><span>يزيد الحمل في أيام التدريب، يخفضه في أيام المراجعة، ويخففه آخر 3 أيام. الأولوية للاختبار الأقرب وللقسم الأضعف.</span></div><div class="s88-timeline">${timeline}</div></section>`;
    o.querySelector('[data-s88-close]')?.addEventListener('click',closePlan);o.classList.add('open');
  }
  function closePlan(){document.getElementById('s88PlanOverlay')?.classList.remove('open');}

  function patchShowPage(){
    if(typeof window.showPage!=='function'||window.__s88ShowPage)return;window.__s88ShowPage=true;const old=window.showPage.bind(window);
    window.showPage=function(id){const r=old.apply(this,arguments);const target=id==='accountPage'?'profilePage':id;if(target==='profilePage'){setTimeout(renderAccount,220);setTimeout(renderAccount,520);}if(target==='tasksPage'){setTimeout(patchTasks,220);setTimeout(patchTasks,520);}return r;};
  }
  function patchAccountRenders(){
    ['s55BackAccount','s55ToggleTheme'].forEach(name=>{const fn=window[name];if(typeof fn!=='function'||window[`__s88_${name}`])return;window[`__s88_${name}`]=true;window[name]=function(){const r=fn.apply(this,arguments);setTimeout(renderAccount,160);return r;};});
  }
  function patchExamFinish(){if(typeof window.finishExam!=='function'||window.__s88Finish)return;window.__s88Finish=true;const old=window.finishExam.bind(window);window.finishExam=function(){const r=old.apply(this,arguments);setTimeout(()=>{loadPlan(true);renderAccount();patchTasks();},260);return r;};}
  function updateVersion(){document.querySelectorAll('.s55-version b').forEach(el=>el.textContent='V.1.0.88');window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;}
  function install(){
    if(installed)return;installed=true;patchShowPage();updateVersion();
    setTimeout(()=>{patchShowPage();patchAccountRenders();patchExamFinish();if(document.getElementById('profilePage')?.classList.contains('active'))renderAccount();if(document.getElementById('tasksPage')?.classList.contains('active'))patchTasks();updateVersion();},180);
    setTimeout(()=>{patchShowPage();patchAccountRenders();patchExamFinish();renderAccount();patchTasks();updateVersion();},650);
    window.addEventListener('suhail:profile-saved',()=>setTimeout(()=>{renderAccount();patchTasks();},180));
    window.SuhailExamPlan88={version:VERSION,settings,saveSettings,buildPlan,loadPlan,openPlan,renderAccount,patchTasks,toggleDone};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
