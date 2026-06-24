/* Suhail Sprint 85 — reliable account completion, route lock, avatar continuity and faster wheel scrolling. */
(function(){
  'use strict';
  const VERSION='87.0.0';
  let internalNavigation=false;
  let setupObserver=null;
  let syncTimer=null;

  function parse(raw,fallback){try{return JSON.parse(raw);}catch(_){return fallback;}}
  function session(){try{return typeof getAuthSession==='function'?getAuthSession():parse(localStorage.getItem('suhail_auth_user')||'null',null);}catch(_){return null;}}
  function userId(){const raw=String(session()?.email||'guest').toLowerCase();return raw.replace(/[^a-z0-9]/g,'_')||'guest';}
  function profile(){return parse(localStorage.getItem(`s54_profile_${userId()}`)||'',{});}
  function authenticated(){const shell=document.getElementById('appShell');const auth=document.getElementById('authPage');return !!session()&&!!shell&&!shell.classList.contains('hidden')&&(!auth||auth.style.display==='none');}
  function onboardingLocked(){const s=session();return !!(authenticated()&&s&&String(s.role||'student')==='student'&&profile().onboardingDone!==true);}
  function activePage(){return document.querySelector('.page.active');}
  function scheduleSync(delay){clearTimeout(syncTimer);syncTimer=setTimeout(syncState,Number(delay)||0);}

  function setupFooter(){
    const screen=document.querySelector('.screen');
    if(!screen)return null;
    let footer=document.getElementById('s85SetupFooter');
    if(!footer){
      footer=document.createElement('div');
      footer.id='s85SetupFooter';
      footer.className='s85-setup-footer';
      footer.hidden=true;
      footer.innerHTML='<button type="button" class="s85-setup-confirm" id="s85SetupConfirm">تأكيد إنشاء الحساب</button>';
      screen.appendChild(footer);
      footer.querySelector('button').addEventListener('click',function(){
        const nativeSave=[...document.querySelectorAll('#studentSetupPage button')].find(b=>/حفظ الرحلة|حفظ وابدأ رحلتي|تأكيد إنشاء الحساب/.test((b.textContent||'').trim())&&!b.classList.contains('s85-setup-confirm'));
        if(typeof window.s54SaveSetup==='function')window.s54SaveSetup();
        else if(nativeSave)nativeSave.click();
      });
    }
    return footer;
  }

  function decorateSetup(){
    const page=document.getElementById('studentSetupPage');
    const shell=page?.querySelector('.s54-page');
    if(!page||!shell)return;
    const locked=onboardingLocked();
    const nativeSave=[...shell.querySelectorAll('button')].find(b=>/حفظ الرحلة|حفظ وابدأ رحلتي/.test((b.textContent||'').trim()));
    if(nativeSave)nativeSave.classList.add('s85-native-save');
    const footer=setupFooter();
    if(footer){
      footer.hidden=!page.classList.contains('active');
      const button=footer.querySelector('#s85SetupConfirm');
      if(button)button.textContent=locked?'تأكيد إنشاء الحساب':'حفظ التغييرات';
    }
    const title=shell.querySelector('.s54-title');
    const subtitle=shell.querySelector('.s54-subtitle');
    if(locked){
      if(title)title.textContent='تأكيد إنشاء الحساب';
      if(subtitle)subtitle.textContent='اختر رحلتك وشخصيتك ثم أكّد للمتابعة';
    }
  }

  function hideSetupFooterUnlessActive(){
    const footer=document.getElementById('s85SetupFooter');
    if(!footer)return;
    footer.hidden=activePage()?.id!=='studentSetupPage';
  }

  function forceSetupRoute(){
    if(!onboardingLocked())return;
    if(activePage()?.id==='studentSetupPage')return;
    if(typeof window.showPage==='function'){
      internalNavigation=true;
      try{window.showPage('studentSetupPage');}finally{internalNavigation=false;}
    }
  }

  function syncState(){
    const locked=onboardingLocked();
    document.body.classList.toggle('s85-onboarding-lock',locked);
    if(locked)forceSetupRoute();
    if(activePage()?.id==='studentSetupPage')decorateSetup();
    else hideSetupFooterUnlessActive();
  }

  function patchNavigation(){
    if(!window.__s85ShowPagePatched&&typeof window.showPage==='function'){
      window.__s85ShowPagePatched=true;
      const previous=window.showPage.bind(window);
      window.showPage=function(id){
        const target=String(id||'');
        if(!internalNavigation&&onboardingLocked()&&target!=='studentSetupPage'){
          internalNavigation=true;
          try{return previous('studentSetupPage');}finally{internalNavigation=false;scheduleSync(20);}
        }
        const result=previous.apply(this,arguments);
        scheduleSync(20);scheduleSync(180);
        return result;
      };
    }
    if(!window.__s85ActivatePagePatched&&typeof window.activatePage==='function'){
      window.__s85ActivatePagePatched=true;
      const previous=window.activatePage.bind(window);
      window.activatePage=function(id){
        const target=String(id||'');
        if(!internalNavigation&&onboardingLocked()&&target!=='studentSetupPage')return previous('studentSetupPage');
        const result=previous.apply(this,arguments);scheduleSync(20);return result;
      };
    }
  }

  function patchSave(){
    if(window.__s85SavePatched||typeof window.s54SaveSetup!=='function')return;
    window.__s85SavePatched=true;
    const previous=window.s54SaveSetup.bind(window);
    window.s54SaveSetup=function(){
      const result=previous.apply(this,arguments);
      setTimeout(function(){
        document.body.classList.remove('s85-onboarding-lock');
        hideSetupFooterUnlessActive();
        /* Home and account both read the same s54 profile key and avatarId. */
        window.dispatchEvent(new CustomEvent('suhail:profile-saved',{detail:{userId:userId(),profile:profile()}}));
        scheduleSync(0);
      },60);
      return result;
    };
  }

  function patchAuth(){
    if(!window.__s85AuthPatched&&typeof window.applyAuthState==='function'){
      window.__s85AuthPatched=true;
      const previous=window.applyAuthState.bind(window);
      window.applyAuthState=function(){const result=previous.apply(this,arguments);scheduleSync(20);return result;};
    }
    if(!window.__s85LogoutPatched&&typeof window.logoutUser==='function'){
      window.__s85LogoutPatched=true;
      const previous=window.logoutUser.bind(window);
      window.logoutUser=function(){const result=previous.apply(this,arguments);document.body.classList.remove('s85-onboarding-lock');hideSetupFooterUnlessActive();scheduleSync(20);return result;};
    }
  }

  function installSetupObserver(){
    const page=document.getElementById('studentSetupPage');
    if(!page||setupObserver)return;
    setupObserver=new MutationObserver(function(){scheduleSync(0);});
    setupObserver.observe(page,{childList:true,subtree:true});
  }

  function normalizeWheelDelta(event,scroller){
    let delta=Number(event.deltaY)||0;
    if(event.deltaMode===1)delta*=18;
    else if(event.deltaMode===2)delta*=Math.max(300,scroller?.clientHeight||600);
    return delta;
  }
  function scrollableAncestor(start,limit){
    let node=start instanceof Element?start:null;
    while(node&&node!==limit){
      if(node.classList?.contains('picker-wheel'))return node;
      const style=getComputedStyle(node);
      if(/auto|scroll/.test(style.overflowY||'')&&node.scrollHeight>node.clientHeight+2)return node;
      node=node.parentElement;
    }
    return null;
  }
  function installFastWheel(){
    const screen=document.querySelector('.screen');
    if(!screen||screen.dataset.s85Wheel==='1')return;
    screen.dataset.s85Wheel='1';
    screen.addEventListener('wheel',function(event){
      if(event.ctrlKey||event.metaKey||Math.abs(event.deltaX)>Math.abs(event.deltaY))return;
      if(event.target.closest('.picker-wheel'))return;
      const auth=document.getElementById('authPage');
      const content=document.querySelector('.content');
      const nested=scrollableAncestor(event.target,screen);
      const authOpen=auth&&auth.classList.contains('active')&&auth.style.display!=='none';
      const scroller=nested||(authOpen?auth:content);
      if(!scroller)return;
      const delta=normalizeWheelDelta(event,scroller);
      if(!delta)return;
      event.preventDefault();
      event.stopImmediatePropagation();
      const multiplier=Math.abs(delta)<14?2.15:2.55;
      scroller.scrollTop+=delta*multiplier;
    },{capture:true,passive:false});
  }

  function updateVersion(){
    document.querySelectorAll('.s55-version b').forEach(el=>el.textContent='V.1.0.87');
    window.SUHAIL_RELEASE=VERSION;
  }

  function install(){
    patchNavigation();patchSave();patchAuth();installSetupObserver();installFastWheel();setupFooter();syncState();updateVersion();
    window.addEventListener('storage',scheduleSync);
    window.addEventListener('suhail:profile-saved',function(){scheduleSync(0);});
    setTimeout(function(){patchNavigation();patchSave();patchAuth();installSetupObserver();installFastWheel();syncState();updateVersion();},450);
    setInterval(function(){patchNavigation();patchSave();syncState();},2500);
    window.SuhailUI85={version:VERSION,sync:syncState,onboardingLocked:onboardingLocked};
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(install,100);},{once:true});
  else setTimeout(install,100);
})();
