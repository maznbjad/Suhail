/* Sprint 63 — persistent, clear home-page test entry. */
(()=>{
  'use strict';
  const BUTTON_ID='s63HomeTestEntry';
  const examIcon=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3h8"/><path d="M9 3v3"/><path d="M15 3v3"/><rect x="4" y="6" width="16" height="15" rx="3"/><path d="m8 13 2.2 2.2L16 9.5"/></svg>`;
  const arrowIcon=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg>`;

  function openTest(){
    if(typeof window.goToExercise==='function') return window.goToExercise();
    if(typeof window.showPage==='function') return window.showPage('exercisePage');
  }

  function installButton(){
    const home=document.getElementById('homePage');
    if(!home || !home.querySelector('[data-s54-home]')) return;
    if(home.querySelector(`#${BUTTON_ID}`)) return;
    const hero=home.querySelector('.s54-hero');
    if(!hero) return;
    const wrap=document.createElement('div');
    wrap.className='s63-test-entry-wrap';
    wrap.id=BUTTON_ID;
    wrap.innerHTML=`<button class="s63-test-entry" type="button" aria-label="فتح الاختبار">
      <span class="s63-test-entry-main"><span class="s63-test-entry-icon">${examIcon}</span><span class="s63-test-entry-label">اختبار</span></span>
      <span class="s63-test-entry-arrow">${arrowIcon}</span>
    </button>`;
    wrap.querySelector('button').addEventListener('click',openTest);
    hero.insertAdjacentElement('afterend',wrap);
  }

  function watch(){
    installButton();
    const home=document.getElementById('homePage');
    if(home && !home.__s63Observer){
      home.__s63Observer=new MutationObserver(()=>requestAnimationFrame(installButton));
      home.__s63Observer.observe(home,{childList:true,subtree:true});
    }
    setInterval(installButton,2000);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',watch);
  else watch();
})();
