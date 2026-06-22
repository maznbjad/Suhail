/* Suhail Sprint 70 — early runtime guard.
   This file must run in <head> before the legacy application script. */
(function () {
  'use strict';

  function memoryStorage() {
    const values = Object.create(null);
    return {
      getItem(key) {
        key = String(key);
        return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
      },
      setItem(key, value) { values[String(key)] = String(value); },
      removeItem(key) { delete values[String(key)]; },
      clear() { Object.keys(values).forEach(key => delete values[key]); },
      key(index) { return Object.keys(values)[Number(index)] || null; },
      get length() { return Object.keys(values).length; }
    };
  }

  try {
    const testKey = '__suhail_storage_test__';
    window.localStorage.setItem(testKey, '1');
    window.localStorage.removeItem(testKey);
  } catch (error) {
    try {
      Object.defineProperty(window, 'localStorage', {
        value: memoryStorage(),
        configurable: true
      });
      window.__SUHAIL_STORAGE_FALLBACK__ = true;
    } catch (_) {
      window.__SUHAIL_STORAGE_FALLBACK__ = true;
    }
  }

  // The splash should never block the application because of an unrelated error.
  window.setTimeout(function () {
    const splash = document.getElementById('suhailSplash');
    if (!splash) return;
    splash.classList.add('hide');
    window.setTimeout(function () { splash.remove(); }, 650);
  }, 4300);

  window.addEventListener('DOMContentLoaded', function () {
    const splash = document.getElementById('suhailSplash');
    if (splash) {
      splash.setAttribute('role', 'status');
      splash.setAttribute('aria-label', 'جاري فتح سهيل');
    }
  }, { once: true });
})();
