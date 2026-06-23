/* Sprint 83 — low-cost runtime guard, deliberately no MutationObserver. */
(function(){
  'use strict';
  const VERSION='83.0.0';
  let released=false;
  function releaseSplash(){
    if(released)return;
    const splash=document.getElementById('suhailSplash');
    if(!splash){released=true;return;}
    splash.classList.add('hide');
    splash.style.pointerEvents='none';
    splash.style.visibility='hidden';
    splash.style.opacity='0';
    setTimeout(()=>{try{splash.remove();}catch(_){/* already gone */}},350);
    released=true;
  }
  function stabilize(){
    document.querySelectorAll('.main-section-title,.main-section-sub').forEach(function(el){
      el.style.removeProperty('visibility');
      el.style.removeProperty('opacity');
    });
  }
  window.addEventListener('load',function(){setTimeout(stabilize,60);setTimeout(releaseSplash,4200);},{once:true});
  document.addEventListener('DOMContentLoaded',function(){setTimeout(stabilize,80);setTimeout(releaseSplash,4600);},{once:true});
  setTimeout(releaseSplash,5200);
  window.SUHAIL_RELEASE=VERSION;
  window.SuhailStable83={version:VERSION,releaseSplash:releaseSplash,stabilize:stabilize};
})();
