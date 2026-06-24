/* Suhail Sprint 107 — runtime verification with no polling and no logical-inset writes. */
(function(){
  'use strict';
  const VERSION='107.0.0';
  const ABSOLUTE_SELECTORS=[
    '.s71-header>.s71-back','.s59-header>.s59-back','.s102-reader>.s102-reader-back',
    '.s54-topbar>.s54-back','.s55-info-header>.s55-info-back','.s39-header>.s39-back',
    '.s28-hero>.s28-back-btn','.s17-hero>.s17-hero-btn.back','.s17-units-hero>.s17-hero-btn.back'
  ].join(',');
  const ALL_SELECTORS=[ABSOLUTE_SELECTORS,'.s101-top>.s101-back','.s47-topbar>.s47-back','.s79-topbar>.s79-back','.s86-top-actions>[data-action="back-unit"]'].join(',');
  function enforce(root=document){
    root.querySelectorAll?.(ABSOLUTE_SELECTORS).forEach(btn=>{
      btn.style.setProperty('right','15px','important');
      btn.style.setProperty('left','auto','important');
      btn.style.removeProperty('inset-inline-start');
      btn.style.removeProperty('inset-inline-end');
    });
  }
  function textRects(container){
    return [...container.querySelectorAll('h1,.s71-header-copy,.s59-header-copy,.s101-top-copy,.s47-page-title,.s54-title,.s55-info-header h1,.s79-heading,.s86-heading')]
      .filter(el=>el.offsetParent!==null).map(el=>el.getBoundingClientRect());
  }
  function verify(){
    const failures=[];
    document.querySelectorAll(ALL_SELECTORS).forEach(btn=>{
      if(btn.offsetParent===null)return;
      const parent=btn.closest('.s71-header,.s59-header,.s101-top,.s102-reader,.s54-topbar,.s55-info-header,.s39-header,.s28-hero,.s17-hero,.s17-units-hero,.s47-topbar,.s79-topbar,.s86-topbar')||btn.parentElement;
      if(!parent)return;
      const br=btn.getBoundingClientRect(),pr=parent.getBoundingClientRect();
      const rightGap=Math.round(pr.right-br.right);
      if(rightGap<0||rightGap>30)failures.push({type:'position',className:btn.className,rightGap});
      for(const tr of textRects(parent)){
        const overlaps=!(br.right<=tr.left||br.left>=tr.right||br.bottom<=tr.top||br.top>=tr.bottom);
        if(overlaps){failures.push({type:'overlap',className:btn.className});break;}
      }
    });
    document.documentElement.dataset.suhailBackGuard=failures.length?'failed':'passed';
    document.documentElement.dataset.suhailRelease=VERSION;
    window.__SUHAIL_BACK_GUARD_FAILURES__=failures;
    return failures;
  }
  function install(){
    enforce();
    const observer=new MutationObserver(records=>{
      for(const r of records)for(const node of r.addedNodes)if(node.nodeType===1)enforce(node);
      requestAnimationFrame(verify);
    });
    observer.observe(document.body,{childList:true,subtree:true});
    requestAnimationFrame(verify);
    window.SuhailBackGuard107={version:VERSION,enforce,verify};
    window.SUHAIL_RELEASE=VERSION;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
