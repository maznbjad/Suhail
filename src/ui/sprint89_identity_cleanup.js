/* Suhail Sprint 89 — canonical account identity and final UI cleanup. */
(function(){
  'use strict';
  const VERSION='89.0.0';
  let installed=false;
  const parse=(raw,fallback)=>{try{return JSON.parse(raw);}catch(_){return fallback;}};
  const normalize=v=>String(v||'').trim().toLowerCase().replace(/^@+/,'').replace(/[^a-z0-9_]/g,'').slice(0,20);
  const session=()=>{try{return typeof getAuthSession==='function'?getAuthSession():parse(localStorage.getItem('suhail_auth_user')||'null',null);}catch(_){return null;}};
  const userId=()=>String(session()?.email||'guest').toLowerCase().replace(/[^a-z0-9]/g,'_')||'guest';
  function currentRecord(){
    const s=session();if(!s)return null;
    try{return (typeof getAllUsers==='function'?getAllUsers():[]).find(x=>String(x.email||'').toLowerCase()===String(s.email||'').toLowerCase())||s;}catch(_){return s;}
  }
  function derivedUsername(){
    const s=session()||{},u=currentRecord()||{};
    return normalize(s.username||u.username||String(s.email||'student').split('@')[0])||'student';
  }
  function syncIdentity(){
    const s=session();if(!s)return null;
    const username=derivedUsername();
    if(normalize(s.username)!==username){
      localStorage.setItem('suhail_auth_user',JSON.stringify({...s,username}));
    }
    const key=`s54_profile_${userId()}`;
    const p=parse(localStorage.getItem(key)||'',{});
    const next={...p,username,ownerEmail:String(s.email||'').toLowerCase()};
    if(s.role==='student'&&s.name)next.displayName=s.name;
    if(s.gender&&!next.gender)next.gender=s.gender;
    localStorage.setItem(key,JSON.stringify(next));
    return {...s,username};
  }
  function cleanSummaryHeader(){
    document.querySelectorAll('.s71-header-icon').forEach(el=>el.remove());
    document.querySelectorAll('.s71-header p,.s71-section-label span').forEach(el=>{
      const t=String(el.textContent||'').trim();
      if(t==='كل القوائم بنفس التصميم وطريقة الاستخدام'||t==='نفس البطاقة في جميع المستويات')el.remove();
    });
  }
  function refreshAccount(){
    syncIdentity();
    if(!document.getElementById('profilePage')?.classList.contains('active'))return;
    try{if(typeof window.s55BackAccount==='function')window.s55BackAccount();}catch(_){}
    setTimeout(()=>{try{window.SuhailExamPlan88?.renderAccount?.();}catch(_){}},80);
  }
  function patchNavigation(){
    if(typeof window.showPage!=='function'||window.__s89ShowPage)return;
    window.__s89ShowPage=true;
    const old=window.showPage.bind(window);
    window.showPage=function(id){
      const result=old.apply(this,arguments);
      const target=id==='accountPage'?'profilePage':id;
      if(target==='profilePage'){setTimeout(refreshAccount,150);setTimeout(refreshAccount,420);}
      if(target==='summariesPage'){setTimeout(cleanSummaryHeader,140);setTimeout(cleanSummaryHeader,360);}
      return result;
    };
  }
  function patchAuth(){
    if(typeof window.applyAuthState==='function'&&!window.__s89AuthState){
      window.__s89AuthState=true;
      const old=window.applyAuthState.bind(window);
      window.applyAuthState=function(){const out=old.apply(this,arguments);setTimeout(syncIdentity,30);return out;};
    }
  }
  function updateVersion(){
    document.querySelectorAll('.s55-version b').forEach(el=>el.textContent='V.1.0.89');
    window.SUHAIL_RELEASE=VERSION;
    document.documentElement.dataset.suhailRelease=VERSION;
  }
  function install(){
    if(installed)return;installed=true;
    syncIdentity();patchAuth();patchNavigation();cleanSummaryHeader();updateVersion();
    if(document.getElementById('profilePage')?.classList.contains('active'))setTimeout(refreshAccount,180);
    window.addEventListener('storage',()=>{syncIdentity();setTimeout(refreshAccount,30);});
    window.addEventListener('suhail:profile-saved',()=>setTimeout(refreshAccount,80));
    setTimeout(()=>{patchAuth();patchNavigation();syncIdentity();cleanSummaryHeader();updateVersion();},650);
    window.SuhailSprint89={version:VERSION,syncIdentity,refreshAccount,cleanSummaryHeader};
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
