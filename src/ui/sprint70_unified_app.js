/* Suhail Sprint 70 — final navigation, onboarding and consistency layer. */
(function () {
  'use strict';
  const VERSION = '72.0.0';
  const backIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg>';

  function activePage() {
    return document.querySelector('.page.active');
  }

  function isAuthenticated() {
    const auth = document.getElementById('authPage');
    const shell = document.getElementById('appShell');
    return !!(shell && !shell.classList.contains('hidden') && auth && auth.style.display === 'none');
  }

  function session() {
    try { return typeof getAuthSession === 'function' ? getAuthSession() : null; }
    catch (_) { return null; }
  }

  function storageGet(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw == null ? fallback : JSON.parse(raw);
    } catch (_) { return fallback; }
  }

  function userId() {
    const email = String(session()?.email || 'guest').toLowerCase();
    return email.replace(/[^a-z0-9]/g, '_') || 'guest';
  }

  function profile() {
    return storageGet(`s54_profile_${userId()}`, {});
  }

  function diagnostics() {
    return storageGet(`s54_diagnostics_${userId()}`, storageGet('s54_diagnostics', {})) || {};
  }

  function unifyBackIcons(root) {
    const base = root || document;
    const selectors = [
      '.s54-back', '.s55-info-back', '.source-back-btn', '.summary-back-btn',
      '.s17-back', '.s16-back', '.s14-back', '.s13-back', '.back-btn'
    ];
    base.querySelectorAll(selectors.join(',')).forEach(button => {
      if (button.dataset.s70Icon === 'back') return;
      button.innerHTML = backIcon;
      button.dataset.s70Icon = 'back';
      if (!button.getAttribute('aria-label')) button.setAttribute('aria-label', 'العودة');
    });
  }

  function decorateSetup(page) {
    const shell = page.querySelector('.s54-page');
    if (!shell) return;
    if (!shell.querySelector('.s70-start-guide')) {
      const topbar = shell.querySelector('.s54-topbar');
      const guide = document.createElement('div');
      guide.className = 's70-start-guide';
      guide.innerHTML = '<span class="s70-guide-icon">4</span><div><b>أربع خطوات وتبدأ</b><span>اختر اختباراتك، حدد مسارك، ثم نوع الحساب والشخصية واحفظ.</span></div>';
      if (topbar) topbar.insertAdjacentElement('afterend', guide);
      else shell.prepend(guide);
    }

    const sections = [...shell.querySelectorAll(':scope > .s54-section')];
    const stepNumbers = [1, 2, 3, 4];
    sections.forEach((section, index) => {
      if (section.querySelector(':scope > .s70-step-badge')) return;
      const badge = document.createElement('span');
      badge.className = 's70-step-badge';
      badge.textContent = String(stepNumbers[index] || index + 1);
      section.prepend(badge);
    });

    const save = [...shell.querySelectorAll('button')].find(button => /حفظ الرحلة|حفظ وابدأ/.test(button.textContent || ''));
    if (save) {
      save.textContent = 'حفظ وابدأ رحلتي';
      save.classList.add('s70-sticky-action');
    }
  }

  function needsFirstGuide() {
    const p = profile();
    const d = diagnostics();
    return !!p.onboardingDone && !d.qudrat && !d.tahsili;
  }

  function decorateHome(page) {
    const home = page.querySelector('.s54-home') || page.querySelector('.s54-page');
    if (!home || !needsFirstGuide()) return;
    if (home.querySelector('.s70-home-guide')) return;
    const hero = home.querySelector('.s54-hero');
    const guide = document.createElement('div');
    guide.className = 's70-home-guide';
    guide.innerHTML = '<span class="mark">1</span><div><b>ابدأ بتحديد مستواك</b><span>بعد القياس سيجهز سهيل خطة اليوم، ثم يرسل أخطاءك إلى المراجعة.</span></div>';
    if (hero) hero.insertAdjacentElement('beforebegin', guide);
    else home.prepend(guide);
  }

  function removeDuplicateNavigation() {
    const finalNav = document.getElementById('s54BottomNav');
    document.querySelectorAll('.suhail-bottom-tabs,.bottom-tabs,.bottom-nav,.s47-bottom-nav').forEach(nav => {
      if (nav !== finalNav) nav.setAttribute('aria-hidden', 'true');
    });
  }

  function updateMode() {
    const page = activePage();
    const auth = !isAuthenticated();
    const onboarding = page?.id === 'studentSetupPage';
    document.body.classList.toggle('s70-auth', auth);
    document.body.classList.toggle('s70-onboarding', !auth && onboarding);

    const finalNav = document.getElementById('s54BottomNav');
    if (finalNav) {
      const shouldHideNav = auth || onboarding || document.body.classList.contains('s54-mode-exam');
      finalNav.classList.toggle('s70-force-hidden', shouldHideNav);
      // Clear the old inline display rule once. Reapplying an inline style while
      // observing style mutations caused an endless update loop in exam mode.
      if (finalNav.style.getPropertyValue('display')) finalNav.style.removeProperty('display');
    }

    if (page) {
      unifyBackIcons(page);
      if (page.id === 'studentSetupPage') decorateSetup(page);
      if (page.id === 'homePage') decorateHome(page);
    }
    removeDuplicateNavigation();
  }

  function patchPageNavigation() {
    if (window.__s70ShowPagePatched || typeof window.showPage !== 'function') return;
    window.__s70ShowPagePatched = true;
    const previous = window.showPage.bind(window);
    window.showPage = function () {
      const result = previous.apply(this, arguments);
      window.setTimeout(updateMode, 0);
      window.setTimeout(updateMode, 160);
      return result;
    };
  }

  function patchAuth() {
    if (!window.__s70AuthPatched && typeof window.applyAuthState === 'function') {
      window.__s70AuthPatched = true;
      const previous = window.applyAuthState.bind(window);
      window.applyAuthState = function () {
        const result = previous.apply(this, arguments);
        window.setTimeout(updateMode, 0);
        return result;
      };
    }
  }

  function install() {
    patchPageNavigation();
    patchAuth();
    updateMode();

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__s70ModeTimer);
      window.__s70ModeTimer = window.setTimeout(updateMode, 30);
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });

    window.addEventListener('storage', updateMode);
    // Historical modules can re-render a page after their own delayed timers.
    // A light idempotent heartbeat guarantees the final layer is restored.
    window.setInterval(updateMode, 2500);
    window.SUHAIL_RELEASE = VERSION;
    window.SuhailUI70 = { update: updateMode, version: VERSION };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { window.setTimeout(install, 120); }, { once: true });
  } else {
    window.setTimeout(install, 120);
  }
})();
