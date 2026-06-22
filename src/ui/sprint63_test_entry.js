/* Sprint 64 — reliable test entry and section chooser. */
(()=>{
  'use strict';
  const BUTTON_ID='s63HomeTestEntry';
  const MODAL_ID='s64TestChooser';
  const examIcon=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3h8"/><path d="M9 3v3"/><path d="M15 3v3"/><rect x="4" y="6" width="16" height="15" rx="3"/><path d="m8 13 2.2 2.2L16 9.5"/></svg>`;
  const arrowIcon=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg>`;

  function closeChooser(){
    const modal=document.getElementById(MODAL_ID);
    if(modal) modal.remove();
  }

  function launchExam(exam){
    closeChooser();
    if(typeof window.openExamSetup==='function'){
      window.openExamSetup(exam);
      return;
    }
    const page=document.getElementById('exercisePage');
    if(page){
      document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
      page.classList.add('active');
    }
  }

  function openTest(){
    closeChooser();
    const modal=document.createElement('div');
    modal.id=MODAL_ID;
    modal.className='s64-test-chooser-backdrop';
    modal.innerHTML=`<section class="s64-test-chooser" role="dialog" aria-modal="true" aria-labelledby="s64TestTitle">
      <button type="button" class="s64-test-close" aria-label="إغلاق">×</button>
      <div class="s64-test-title" id="s64TestTitle">اختبار</div>
      <div class="s64-test-grid">
        <button type="button" class="s64-test-choice tahsili" data-exam="تحصيلي"><span class="s64-choice-symbol">⚗</span><span>تحصيلي</span></button>
        <button type="button" class="s64-test-choice" data-exam="قدرات كمي"><span class="s64-choice-symbol">∑</span><span>قدرات كمي</span></button>
        <button type="button" class="s64-test-choice green" data-exam="قدرات لفظي"><span class="s64-choice-symbol">ض</span><span>قدرات لفظي</span></button>
      </div>
    </section>`;
    document.body.appendChild(modal);
    modal.querySelector('.s64-test-close').addEventListener('click',closeChooser);
    modal.addEventListener('click',e=>{ if(e.target===modal) closeChooser(); });
    modal.querySelectorAll('[data-exam]').forEach(btn=>btn.addEventListener('click',()=>launchExam(btn.dataset.exam)));
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

  window.s64OpenTestChooser=openTest;
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',watch);
  else watch();
})();
