/* Suhail Sprint 56 — boot the selected theme before all pages render. */
(function(){
  'use strict';
  const KEY='s55_theme';
  function isDark(){try{return localStorage.getItem(KEY)==='dark';}catch(_){return false;}}
  function apply(){
    const dark=isDark();
    document.documentElement.setAttribute('data-theme',dark?'dark':'light');
    if(document.body)document.body.classList.toggle('s55-dark',dark);
    let meta=document.querySelector('meta[name="theme-color"]');
    if(!meta){meta=document.createElement('meta');meta.name='theme-color';document.head.appendChild(meta);}
    meta.content=dark?'#07111c':'#f6fafe';
    document.documentElement.style.backgroundColor=dark?'#07111c':'#f6fafe';
  }
  window.SuhailTheme={apply,isDark,set(mode){try{localStorage.setItem(KEY,mode==='dark'?'dark':'light');}catch(_){}apply();}};
  apply();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
  window.addEventListener('storage',e=>{if(e.key===KEY)apply();});
  const observer=new MutationObserver(()=>{
    const expected=isDark();
    if(document.body&&document.body.classList.contains('s55-dark')!==expected)apply();
  });
  if(document.documentElement)observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme'],childList:true,subtree:false});
})();
