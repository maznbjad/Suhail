/* Suhail Sprint 87 — meaningful streak shields and character reactions. */
(function(){
  'use strict';
  const VERSION='87.0.0';
  const DAY=86400000;
  const MAX_SHIELDS=2;
  const AVATARS=__S87_AVATARS__;
  const PORTRAITS=__S87_AVATAR_PORTRAITS__;
  const HALF=__S87_AVATAR_HALF__;
  let reactionTimer=null;
  let installed=false;

  const parse=(raw,fallback)=>{try{return JSON.parse(raw);}catch(_){return fallback;}};
  const session=()=>{try{return typeof getAuthSession==='function'?getAuthSession():parse(localStorage.getItem('suhail_auth_user')||'null',null);}catch(_){return null;}};
  const userId=()=>String(session()?.email||'guest').toLowerCase().replace(/[^a-z0-9]/g,'_')||'guest';
  const key=()=>`s87_motivation_${userId()}`;
  const today=(d=new Date())=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const month=(d=new Date())=>today(d).slice(0,7);
  const dateFrom=s=>{const [y,m,d]=String(s).split('-').map(Number);return new Date(y,m-1,d);};
  const diffDays=(a,b)=>Math.round((dateFrom(b)-dateFrom(a))/DAY);
  const addDays=(s,n)=>{const d=dateFrom(s);d.setDate(d.getDate()+n);return today(d);};
  const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

  function profile(){
    const id=userId();
    const p54=parse(localStorage.getItem(`s54_profile_${id}`)||'',{});
    const p47=parse(localStorage.getItem(`s47_profile_${id}`)||'',{});
    const s=session()||{};
    const avatarId=p54.avatarId||p47.avatarId||(s.gender==='female'?'female_01':(AVATARS.default||'male_02'));
    return {displayName:p54.displayName||p47.displayName||s.name||'طالب سهيل',avatarId,onboardingDone:p54.onboardingDone===true||p47.onboardingDone===true||s.role!=='student'};
  }
  function avatarSrc(kind='portrait'){
    const id=profile().avatarId;
    return (kind==='half'?HALF[id]:PORTRAITS[id])||PORTRAITS[AVATARS.default]||HALF[AVATARS.default]||'';
  }
  function ready(){const s=session(),p=profile();return !!s&&String(s.role||'student')==='student'&&p.onboardingDone===true;}

  function legacyActivity(){
    const k=`s47_activity_${userId()}`;
    const v=parse(localStorage.getItem(k)||'',{dates:[],events:[],lastAt:0});
    return {key:k,value:v&&typeof v==='object'?v:{dates:[],events:[],lastAt:0}};
  }
  function baseState(){return {version:1,activeDates:[],protectedDates:[],shields:MAX_SHIELDS,shieldMonth:month(),lastActivityAt:0,pendingRescue:null,dismissedRescue:'',lastWelcomeKey:'',planCelebratedDate:''};}
  function load(){
    const st=Object.assign(baseState(),parse(localStorage.getItem(key())||'',{}));
    const legacy=legacyActivity().value;
    st.protectedDates=[...new Set(st.protectedDates||[])].filter(Boolean).sort().slice(-40);
    const protectedSet=new Set(st.protectedDates);
    const merged=new Set([...(st.activeDates||[]),...(legacy.dates||[]).filter(d=>!protectedSet.has(d))]);
    st.activeDates=[...merged].filter(Boolean).sort().slice(-500);
    if(st.shieldMonth!==month()){st.shieldMonth=month();st.shields=MAX_SHIELDS;st.pendingRescue=null;}
    st.shields=Math.max(0,Math.min(MAX_SHIELDS,Number(st.shields??MAX_SHIELDS)));
    save(st,false);
    return st;
  }
  function save(st,syncLegacy=true){
    try{localStorage.setItem(key(),JSON.stringify(st));}catch(_){}
    if(syncLegacy){
      const legacy=legacyActivity();
      legacy.value.dates=[...new Set([...(legacy.value.dates||[]),...(st.activeDates||[]),...(st.protectedDates||[])])].sort().slice(-500);
      legacy.value.lastAt=Math.max(Number(legacy.value.lastAt||0),Number(st.lastActivityAt||0));
      try{localStorage.setItem(legacy.key,JSON.stringify(legacy.value));}catch(_){}
    }
    try{localStorage.setItem('suhail_streak_days',String(streak(st).count));}catch(_){}
  }
  function allDates(st){return new Set([...(st.activeDates||[]),...(st.protectedDates||[])]);}
  function streak(st=load()){
    const set=allDates(st),t=today();
    let cursor=set.has(t)?t:addDays(t,-1),count=0;
    for(let i=0;i<500;i++){if(!set.has(cursor))break;count++;cursor=addDays(cursor,-1);}
    return {count,hasToday:set.has(t)};
  }
  function lastBeforeToday(st){return [...new Set(st.activeDates||[])].filter(d=>d<today()).sort().pop()||'';}
  function rescueInfo(st=load()){
    const last=lastBeforeToday(st);if(!last)return null;
    const gap=diffDays(last,today()),missed=Math.max(0,gap-1);
    if(missed<1)return null;
    const signature=`${last}:${today()}:${missed}`;
    if(st.dismissedRescue===signature)return null;
    const canUse=missed<=2&&missed<=st.shields;
    return {last,gap,missed,signature,canUse};
  }
  function evaluateReturn(showPrompt=true){
    if(!ready())return;
    const st=load(),info=rescueInfo(st);if(!info)return;
    st.pendingRescue=info;save(st);
    if(st.lastWelcomeKey===info.signature)return;
    st.lastWelcomeKey=info.signature;save(st);
    if(info.canUse){
      showReaction('return',`رجعت، وهذا أهم شيء. فاتك ${info.missed===1?'يوم واحد':info.missed+' أيام'} ويمكن لدرع السلسلة حمايتها.`,{title:'سهيل معك',actionLabel:'عرض الدرع',action:openShieldPanel,sticky:true});
    }else{
      showReaction('return','عودتك أهم من الأيام التي فاتتك. نبدأ اليوم بخطوة قصيرة ونبني سلسلة جديدة.',{title:'بداية جديدة',actionLabel:'ابدأ الآن',action:()=>{try{goToExercise();}catch(_){}},sticky:true});
    }
  }

  function recordActivity(type='learning'){
    if(!ready())return;
    const st=load(),t=today(),first=!st.activeDates.includes(t);
    if(first)st.activeDates.push(t);
    st.lastActivityAt=Date.now();
    save(st);
    if(first)showReaction('streak','تم تثبيت إنجاز اليوم في سلسلتك 🔥',{title:'خطوة محسوبة'});
    patchHome();
    return {first,type,streak:streak(st).count};
  }

  function useShield(){
    const st=load(),info=st.pendingRescue||rescueInfo(st);
    if(!info||!info.canUse||st.shields<info.missed){showReaction('warn','لا يوجد درع كافٍ لهذه الفترة. ابدأ سلسلة جديدة من اليوم.',{title:'ابدأ من جديد'});closeShieldPanel();return;}
    for(let i=1;i<=info.missed;i++)st.protectedDates.push(addDays(info.last,i));
    st.protectedDates=[...new Set(st.protectedDates)].sort();
    st.shields-=info.missed;st.pendingRescue=null;st.dismissedRescue=info.signature;save(st);
    closeShieldPanel();
    showReaction('celebrate',`حُفظت سلسلتك باستخدام ${info.missed===1?'درع واحد':info.missed+' درعين'}. بقي لديك ${st.shields}.`,{title:'السلسلة محمية',celebrate:true,sticky:true});
    patchHome();
  }
  function declineShield(){
    const st=load(),info=st.pendingRescue||rescueInfo(st);if(info)st.dismissedRescue=info.signature;
    st.pendingRescue=null;save(st);closeShieldPanel();
    showReaction('return','ممتاز، نبدأ سلسلة جديدة من اليوم. المهم أنك رجعت.',{title:'بداية جديدة'});
  }

  function reactionHost(){return document.querySelector('.screen')||document.body;}
  function ensureReaction(){
    let el=document.getElementById('s87Reaction');if(el)return el;
    el=document.createElement('div');el.id='s87Reaction';el.className='s87-reaction';reactionHost().appendChild(el);return el;
  }
  function confetti(){return `<div class="s87-confetti">${Array.from({length:14},(_,i)=>`<i style="left:${5+i*6.7}%;animation-delay:${(i%5)*.08}s;background:${['#2f83e8','#42c989','#f6ba3b','#a56ce6'][i%4]}"></i>`).join('')}</div>`;}
  function showReaction(type,text,opts={}){
    if(!ready()&&!opts.force)return;
    const el=ensureReaction(),title=opts.title||({correct:'أحسنت!',wrong:'نكمل بهدوء',neutral:'تم تسجيل الإجابة',celebrate:'إنجاز رائع',return:'مرحبًا بعودتك',shield:'درع السلسلة',streak:'استمر'}[type]||'سهيل معك');
    el.className=`s87-reaction s87-${type} ${type==='celebrate'?'celebrate':''} ${type==='wrong'||type==='warn'?'warn':''}`;
    el.innerHTML=`${opts.celebrate?confetti():''}<button class="s87-reaction-close" type="button" aria-label="إغلاق">×</button><div class="s87-reaction-avatar"><img src="${avatarSrc(opts.celebrate?'half':'portrait')}" alt="الشخصية المختارة"></div><div class="s87-reaction-copy"><b>${esc(title)}</b><span>${esc(text)}</span></div>${opts.actionLabel?`<button type="button" class="s87-reaction-action">${esc(opts.actionLabel)}</button>`:'<span></span>'}`;
    el.querySelector('.s87-reaction-close')?.addEventListener('click',hideReaction);
    if(opts.actionLabel&&typeof opts.action==='function')el.querySelector('.s87-reaction-action')?.addEventListener('click',()=>{hideReaction();opts.action();});
    requestAnimationFrame(()=>el.classList.add('show'));
    clearTimeout(reactionTimer);if(!opts.sticky)reactionTimer=setTimeout(hideReaction,opts.celebrate?4800:2700);
  }
  function hideReaction(){const el=document.getElementById('s87Reaction');if(el)el.classList.remove('show');clearTimeout(reactionTimer);}

  function ensureModal(){
    let o=document.getElementById('s87ShieldOverlay');if(o)return o;
    o=document.createElement('div');o.id='s87ShieldOverlay';o.className='s87-modal-overlay';reactionHost().appendChild(o);
    o.addEventListener('click',e=>{if(e.target===o)closeShieldPanel();});return o;
  }
  function openShieldPanel(){
    if(!ready())return;
    const st=load(),s=streak(st),info=st.pendingRescue||rescueInfo(st),o=ensureModal();
    const rescue=info?`<div class="s87-rescue-box"><b>${info.canUse?'يمكن حماية سلسلتك الآن':'هذه الفترة أطول من حماية الدرع'}</b><p>${info.canUse?`فاتك ${info.missed===1?'يوم واحد':info.missed+' أيام'}، وسيُخصم ${info.missed===1?'درع واحد':info.missed+' درعين'}.`:'الدرع يحمي يومًا واحدًا، وبحد أقصى يومين متتاليين عند توفر درعين.'}</p></div>`:'';
    o.innerHTML=`<section class="s87-modal" role="dialog" aria-modal="true" aria-label="درع السلسلة"><div class="s87-modal-head"><div class="s87-modal-avatar"><img src="${avatarSrc('half')}" alt="الشخصية المختارة"></div><div class="s87-modal-title"><b>درع السلسلة</b><span>يحمي إنجازك عند غياب قصير، ولا يُحتسب لمجرد فتح التطبيق.</span></div><button class="s87-modal-x" type="button" aria-label="إغلاق">×</button></div><div class="s87-shield-balance"><div class="s87-shield-box"><strong>🔥 ${s.count}</strong><span>يومًا في السلسلة</span></div><div class="s87-shield-box"><strong>🛡 ${st.shields}/${MAX_SHIELDS}</strong><span>الرصيد هذا الشهر</span></div></div>${rescue}<div class="s87-rule-list"><div class="s87-rule"><i>✓</i><span>يُثبت اليوم عند حل سؤال أو إنجاز نشاط تعليمي، وليس عند فتح التطبيق.</span></div><div class="s87-rule"><i>🛡</i><span>كل درع يحمي يوم غياب واحد، ويتجدد الرصيد إلى درعين مع بداية كل شهر.</span></div><div class="s87-rule"><i>↺</i><span>إذا طال الانقطاع أكثر من يومين تبدأ سلسلة جديدة برسالة تشجيعية دون عقوبة.</span></div></div>${info?`<div class="s87-modal-actions">${info.canUse?'<button class="primary" type="button" data-s87-use>استخدم الدرع</button>':''}<button class="secondary" type="button" data-s87-decline>${info.canUse?'ابدأ من جديد':'حسنًا'}</button></div>`:'<div class="s87-modal-actions"><button class="primary" type="button" data-s87-close>ممتاز</button></div>'}</section>`;
    o.querySelector('.s87-modal-x')?.addEventListener('click',closeShieldPanel);o.querySelector('[data-s87-close]')?.addEventListener('click',closeShieldPanel);o.querySelector('[data-s87-use]')?.addEventListener('click',useShield);o.querySelector('[data-s87-decline]')?.addEventListener('click',declineShield);o.classList.add('open');
  }
  function closeShieldPanel(){document.getElementById('s87ShieldOverlay')?.classList.remove('open');}

  function homeMessage(st,s){
    if(st.pendingRescue?.canUse)return `لديك فرصة لحماية السلسلة باستخدام ${st.pendingRescue.missed===1?'درع':'درعين'}.`;
    if(s.hasToday)return 'تم تثبيت إنجاز اليوم؛ خذ الخطوة التالية بهدوء.';
    if(s.count)return 'حل سؤالًا واحدًا أو أنجز نشاطًا لتثبيت يومك.';
    return 'ابدأ أول يوم في رحلتك بنشاط قصير.';
  }
  function patchHome(){
    const page=document.getElementById('homePage');if(!page||!ready())return;
    const target=page.querySelector('.s18-stats')||page.querySelector('.s47-kpis')||page.querySelector('.home-quick-row');if(!target)return;
    let card=page.querySelector('.s87-motivation-card');if(!card){card=document.createElement('section');card.className='s87-motivation-card';target.insertAdjacentElement('afterend',card);}
    const st=load(),s=streak(st),risk=!!st.pendingRescue;
    card.innerHTML=`<div class="s87-motivation-avatar"><img src="${avatarSrc('half')}" alt="الشخصية المختارة"></div><div class="s87-motivation-copy"><b>رحلة سهيل</b><span>${esc(homeMessage(st,s))}</span></div><div class="s87-motivation-metrics"><div class="s87-metric ${risk?'risk':''}"><strong>🔥 ${s.count}</strong><small>السلسلة</small></div><div class="s87-metric shield"><strong>🛡 ${st.shields}</strong><small>الدرع</small></div></div>`;
    card.onclick=openShieldPanel;
  }

  function checkPlanCompletion(){
    if(!ready())return false;
    const plan=parse(localStorage.getItem(`s39_daily_plans_${userId()}`)||'',{}),d=plan[today()]||{};
    let complete=false;
    const visible=[...document.querySelectorAll('#tasksPage .s39-task')];
    if(visible.length)complete=visible.every(x=>x.classList.contains('done'));
    else complete=['practice','errors','summary'].every(k=>d[k]===true);
    if(!complete)return false;
    const st=load();if(st.planCelebratedDate===today())return true;
    st.planCelebratedDate=today();save(st);recordActivity('daily-plan');
    showReaction('celebrate','أنجزت خطة اليوم كاملة. خذ راحتك الآن؛ الاستمرار أهم من الضغط.',{title:'خطة اليوم مكتملة 🎉',celebrate:true,sticky:true});
    return true;
  }

  function answerReaction(correct){
    recordActivity('answer');
    if(window.SUHAIL_SHOW_RESULT===false){showReaction('neutral','تم تسجيل إجابتك. أكمل السؤال التالي بثقة.');return;}
    if(correct){
      const msgs=['فهمك يتقدم، استمر بنفس التركيز.','إجابة صحيحة؛ ثبّت سبب الاختيار قبل الانتقال.','ممتاز! اخترت الفكرة المناسبة للسؤال.'];
      showReaction('correct',msgs[Math.floor(Math.random()*msgs.length)]);
    }else{
      const msgs=['الخطأ هنا مفيد؛ راجع الفكرة ثم جرّب سؤالًا مشابهًا.','قريب. ركز على المطلوب والمعطيات قبل اختيار العلاقة.','لا بأس؛ افهم سبب الخطأ بدل حفظ الإجابة.'];
      showReaction('wrong',msgs[Math.floor(Math.random()*msgs.length)]);
    }
  }

  function wrap(name,wrapperFlag,make){
    const fn=window[name];if(typeof fn!=='function'||window[wrapperFlag])return;window[wrapperFlag]=true;window[name]=make(fn.bind(window));
  }
  function installHooks(){
    wrap('answerQuiz','__s87AnswerQuiz',old=>function(button,index,correct){const r=old.apply(this,arguments);setTimeout(()=>answerReaction(!!correct),20);return r;});
    wrap('finishExam','__s87FinishExam',old=>function(){const r=old.apply(this,arguments);setTimeout(()=>{recordActivity('exam');let total=0,correct=0;try{total=activeQuestions.length;correct=questionResults.filter(x=>x.correct).length;}catch(_){}const pct=total?Math.round(correct/total*100):0;if(pct>=90)showReaction('celebrate',`أنهيت الاختبار بدقة ${pct}%. أداء قوي جدًا.`,{title:'أبدعت في الاختبار 🎉',celebrate:true});else if(pct>=70)showReaction('correct',`نتيجتك ${pct}%. راجع الأخطاء القليلة وارجع أقوى.`,{title:'تقدم واضح'});else showReaction('wrong',`نتيجتك ${pct}%. ابدأ بأضعف مهارة وراجعها دون استعجال.`,{title:'هذه نقطة بداية'});checkPlanCompletion();},180);return r;});
    wrap('s39ToggleTask','__s87PlanToggle',old=>function(){const r=old.apply(this,arguments);setTimeout(checkPlanCompletion,120);return r;});
    [['s13Answer','__s87s13'],['s14Answer','__s87s14'],['s16Answer','__s87s16'],['s17Answer','__s87s17']].forEach(([n,f])=>wrap(n,f,old=>function(btn,i,c){const r=old.apply(this,arguments);setTimeout(()=>answerReaction(Number(i)===Number(c)),20);return r;}));
    if(typeof window.showPage==='function'&&!window.__s87ShowPage){window.__s87ShowPage=true;const old=window.showPage.bind(window);window.showPage=function(id){const r=old.apply(this,arguments);setTimeout(()=>{if(id==='homePage')patchHome();if(id==='tasksPage')checkPlanCompletion();},120);return r;};}
    if(typeof window.applyAuthState==='function'&&!window.__s87Auth){window.__s87Auth=true;const old=window.applyAuthState.bind(window);window.applyAuthState=function(){const r=old.apply(this,arguments);setTimeout(()=>{evaluateReturn(true);patchHome();},180);return r;};}
  }
  function installDelegated(){
    if(document.documentElement.dataset.s87Delegated==='1')return;document.documentElement.dataset.s87Delegated='1';
    document.addEventListener('click',e=>{
      const btn=e.target.closest?.('[data-question-index][data-option-index]');if(!btn)return;
      try{
        const qi=Number(btn.dataset.questionIndex),oi=Number(btn.dataset.optionIndex),state=window.SuhailPhysics86?.state;
        const sid=state?.summaryId,summary=(window.smartSummaries||[]).find(x=>String(x.summary_id||x.id)===String(sid));
        const q=summary?.learning_path_v2?.practice_questions?.[qi];if(q)setTimeout(()=>answerReaction(oi===Number(q.correct_index)),30);
      }catch(_){}
      setTimeout(checkPlanCompletion,180);
    },true);
  }

  function updateVersion(){
    document.querySelectorAll('.s55-version b').forEach(el=>el.textContent='V.1.0.87');
    window.SUHAIL_RELEASE=VERSION;document.documentElement.dataset.suhailRelease=VERSION;
  }
  function install(){
    if(window.SUHAIL_FOCUS_MODE)return;
    if(installed)return;installed=true;load();installHooks();installDelegated();updateVersion();
    setTimeout(()=>{installHooks();evaluateReturn(true);patchHome();checkPlanCompletion();},350);
    window.addEventListener('suhail:profile-saved',()=>setTimeout(()=>{load();patchHome();},80));
    window.addEventListener('storage',()=>setTimeout(patchHome,50));
    window.SuhailMotivation87={version:VERSION,state:load,streak:()=>streak(load()),recordActivity,openShieldPanel,useShield,declineShield,showReaction,patchHome,checkPlanCompletion,evaluateReturn};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
