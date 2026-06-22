/* Suhail Sprints 40-47: navigation, profile-aware diagnostics, streak rescue,
   challenges, avatars, deep admin settings and final UX/performance polish. */
(function () {
  'use strict';
  const VERSION = '47.0.0';
  const DAY = 86400000;
  const DEFAULT_ADMIN = __S47_ADMIN_SETTINGS__;
  const AVATAR_CATALOG = __S47_AVATARS__;
  const AVATAR_ASSETS = __S47_AVATAR_ASSETS__;
  const CHALLENGE_CATALOG = __S47_CHALLENGES__;
  const SCORE_CATALOG = __S47_SCORE_MODELS__;
  const CUSTOM_PAGES = new Set(['studentSetupPage', 'diagnosticChoicePage', 's47DiagnosticPage', 'challengePage', 'adminSettingsPage']);
  let diagnosticState = null;
  let setupDraft = null;
  let adminTab = 'overview';
  let navObserverTimer = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[ch]));
  }
  function safeParse(raw, fallback) { try { return JSON.parse(raw); } catch (_) { return fallback; } }
  function deepClone(value) { return safeParse(JSON.stringify(value), {}); }
  function deepMerge(base, override) {
    const out = Array.isArray(base) ? base.slice() : { ...(base || {}) };
    Object.entries(override || {}).forEach(([key, value]) => {
      if (value && typeof value === 'object' && !Array.isArray(value) && out[key] && typeof out[key] === 'object' && !Array.isArray(out[key])) out[key] = deepMerge(out[key], value);
      else out[key] = value;
    });
    return out;
  }
  function session() { try { return typeof getAuthSession === 'function' ? getAuthSession() : null; } catch (_) { return null; } }
  function isAdmin() { const s = session(); return !!(s && s.role === 'admin'); }
  function userId() {
    const s = session();
    const raw = (s && s.email) ? String(s.email).toLowerCase() : 'guest';
    return raw.replace(/[^a-z0-9]/g, '_') || 'guest';
  }
  function key(name) { return `s47_${name}_${userId()}`; }
  function read(name, fallback) { return safeParse(localStorage.getItem(key(name)) || '', fallback); }
  function write(name, value) { localStorage.setItem(key(name), JSON.stringify(value)); }
  function todayLocal(date) {
    const d = date || new Date();
    const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  function pct(a, b) { return b ? Math.round((Number(a || 0) / Number(b)) * 100) : 0; }
  function clamp(n, min, max) { return Math.max(min, Math.min(max, Number(n || 0))); }
  function avg(values) { return values.length ? values.reduce((a, b) => a + Number(b || 0), 0) / values.length : 0; }
  function hash(text) { let h = 2166136261; for (const c of String(text)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0); }
  function toast(message) {
    let el = document.getElementById('s47Toast');
    if (!el) { el = document.createElement('div'); el.id = 's47Toast'; el.className = 's47-toast'; const screen = document.querySelector('.screen') || document.body; screen.appendChild(el); }
    el.textContent = message; el.classList.add('show'); clearTimeout(el._timer); el._timer = setTimeout(() => el.classList.remove('show'), 1900);
  }
  function ensurePage(id) {
    let page = document.getElementById(id);
    if (!page) { page = document.createElement('div'); page.id = id; page.className = 'page'; const content = document.querySelector('.content'); if (content) content.appendChild(page); }
    return page;
  }
  function activate(id) {
    if (typeof activatePage === 'function') activatePage(id);
    else { document.querySelectorAll('.page').forEach(p => p.classList.remove('active')); const p = ensurePage(id); p.classList.add('active'); }
    requestAnimationFrame(refreshNavigationMode);
  }
  function activePage() { return document.querySelector('.page.active'); }
  function backIcon() { return '<svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>'; }
  function chevronUp() { return '<svg viewBox="0 0 24 24"><path d="m6 15 6-6 6 6"/></svg>'; }
  function icon(name) {
    const icons = {
      home:'<svg viewBox="0 0 24 24"><path d="M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/></svg>',
      review:'<svg viewBox="0 0 24 24"><path d="M5 4h12a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2Z"/><path d="M5 17a3 3 0 0 1 3-3h11"/><path d="M9 8h6"/></svg>',
      summaries:'<svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6Z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h6"/></svg>',
      tasks:'<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="17" rx="3"/><path d="M8 9h8M8 14h5"/><path d="m15 16 1.5 1.5L20 14"/></svg>',
      profile:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
      challenge:'<svg viewBox="0 0 24 24"><path d="M8 4h8v5a4 4 0 0 1-8 0Z"/><path d="M8 6H5v2a3 3 0 0 0 3 3M16 6h3v2a3 3 0 0 1-3 3M12 13v4M8 21h8M9 17h6"/></svg>',
      bell:'<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>',
      edit:'<svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16Z"/><path d="m13 7 4 4"/></svg>',
      settings:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 14a2 2 0 0 0 .4 2.2l.1.1-2.2 2.2-.1-.1A2 2 0 0 0 15 18l-.5.2V21h-3v-2.8L11 18a2 2 0 0 0-2.2.4l-.1.1-2.2-2.2.1-.1A2 2 0 0 0 7 14l-.2-.5H4v-3h2.8L7 10a2 2 0 0 0-.4-2.2l-.1-.1 2.2-2.2.1.1A2 2 0 0 0 11 6l.5-.2V3h3v2.8L15 6a2 2 0 0 0 2.2-.4l.1-.1 2.2 2.2-.1.1A2 2 0 0 0 19 10l.2.5H22v3h-2.8Z"/></svg>'
    };
    return icons[name] || icons.home;
  }
  function topbar(title, subtitle, action) {
    return `<div class="s47-topbar"><div><div class="s47-page-title">${esc(title)}</div>${subtitle ? `<div class="s47-page-sub">${esc(subtitle)}</div>` : ''}</div><button class="s47-back" onclick="${action || "showPage('homePage')"}" aria-label="العودة">${backIcon()}</button></div>`;
  }

  function avatarItems() { return Array.isArray(AVATAR_CATALOG.items) ? AVATAR_CATALOG.items.filter(x => x.enabled !== false) : []; }
  function avatarSrc(id) { return AVATAR_ASSETS[id] || AVATAR_ASSETS[AVATAR_CATALOG.default] || ''; }
  function profileExists() { return !!localStorage.getItem(key('profile')); }
  function defaultProfile() {
    const s = session() || {};
    return { displayName: s.name || 'طالب سهيل', academicTrack: 'scientific', targetExam: 'qudrat', avatarId: AVATAR_CATALOG.default || 'male_01', onboardingDone: false, updatedAt: Date.now() };
  }
  function getProfile() { return deepMerge(defaultProfile(), read('profile', {})); }
  function saveProfile(profile) {
    const value = { ...getProfile(), ...(profile || {}), onboardingDone: true, updatedAt: Date.now() };
    write('profile', value);
    try { const s = session(); if (s && typeof setAuthSession === 'function') setAuthSession({ ...s, name: value.displayName || s.name }); } catch (_) {}
    return value;
  }
  function trackLabel(track) { return track === 'literary' ? 'أدبي' : 'علمي'; }
  function targetLabel(target) { return target === 'tahsili' ? 'التحصيلي' : 'القدرات'; }
  function friendCode() { return `SH-${String(hash(userId())).slice(-6).padStart(6, '0')}`; }

  function getAdminSettings() { return deepMerge(deepClone(DEFAULT_ADMIN), safeParse(localStorage.getItem('s47_admin_settings') || '', {})); }
  function saveAdminSettings(settings) { localStorage.setItem('s47_admin_settings', JSON.stringify(settings)); }
  function getPath(obj, path) { return String(path).split('.').reduce((acc, part) => acc == null ? undefined : acc[part], obj); }
  function setPath(obj, path, value) { const parts = String(path).split('.'); let cursor = obj; parts.slice(0, -1).forEach(part => { if (!cursor[part] || typeof cursor[part] !== 'object') cursor[part] = {}; cursor = cursor[part]; }); cursor[parts[parts.length - 1]] = value; return obj; }

  function navItems() {
    return [
      { id:'review', label:'المراجعة', icon:'review', action:"showPage('reviewPage')", pages:['reviewPage','errorReviewPage'] },
      { id:'summaries', label:'الملخصات', icon:'summaries', action:"s28SummariesGateway()", pages:['summariesPage','skillHubPage'] },
      { id:'home', label:'الرئيسية', icon:'home', action:"showPage('homePage')", pages:['homePage'] },
      { id:'tasks', label:'المهام', icon:'tasks', action:"showPage('tasksPage')", pages:['tasksPage','statsPage'] },
      { id:'profile', label:'الحساب', icon:'profile', action:"showPage('profilePage')", pages:['profilePage','studentSetupPage','adminSettingsPage','questionManagementPage','aiGeneratorPage','challengePage','friendsPage'] }
    ];
  }
  function renderNavButtons(lift) {
    return navItems().map(item => lift
      ? `<button data-nav="${item.id}" onclick="${item.action};document.body.classList.remove('s47-lift-open')">${icon(item.icon)}<span>${item.label}</span></button>`
      : `<button class="s47-nav-btn ${item.id === 'home' ? 'home' : ''}" data-nav="${item.id}" onclick="${item.action}">${item.id === 'home' ? `<span class="s47-nav-home-bubble">${icon('home')}</span><span>الرئيسية</span>` : `${icon(item.icon)}<span>${item.label}</span>`}</button>`
    ).join('');
  }
  function ensureNavigation() {
    const screen = document.querySelector('.screen'); if (!screen) return;
    let nav = document.getElementById('s47BottomNav');
    if (!nav) { nav = document.createElement('nav'); nav.id = 's47BottomNav'; nav.className = 's47-bottom-nav'; nav.setAttribute('aria-label', 'القائمة الرئيسية'); nav.innerHTML = renderNavButtons(false); screen.appendChild(nav); }
    let lift = document.getElementById('s47SummaryLift');
    if (!lift) { lift = document.createElement('div'); lift.id = 's47SummaryLift'; lift.className = 's47-summary-lift'; lift.innerHTML = `<button class="s47-lift-handle" aria-label="إظهار القائمة" onclick="document.body.classList.toggle('s47-lift-open')">${chevronUp()}</button><div class="s47-lift-panel">${renderNavButtons(true)}</div>`; screen.appendChild(lift); }
  }
  function examInProgress() { try { return typeof isExamInProgress === 'function' && isExamInProgress(); } catch (_) { return false; } }
  function summaryIsDetail(page) {
    if (!page || page.id !== 'summariesPage') return false;
    return !!page.querySelector('.s13-lesson-hero,.s13-cardline,.s17-lesson-detail,.summary-detail-view,[data-summary-detail="true"]');
  }
  function refreshNavigationMode() {
    ensureNavigation();
    const page = activePage(); const id = page ? page.id : 'homePage';
    const diagnosticQuestion = id === 's47DiagnosticPage' && diagnosticState && !diagnosticState.finished;
    const examMode = (id === 'exercisePage' && examInProgress()) || diagnosticQuestion;
    const summaryDetail = !examMode && summaryIsDetail(page);
    document.body.classList.toggle('s47-exam-mode', examMode);
    document.body.classList.toggle('s47-summary-detail', summaryDetail);
    if (!summaryDetail) document.body.classList.remove('s47-lift-open');
    document.querySelectorAll('#s47BottomNav .s47-nav-btn').forEach(btn => btn.classList.remove('active'));
    const item = navItems().find(x => x.pages.includes(id));
    const activeId = item ? item.id : (id === 'homePage' ? 'home' : '');
    if (activeId) { const btn = document.querySelector(`#s47BottomNav [data-nav="${activeId}"]`); if (btn) btn.classList.add('active'); }
    const content = document.querySelector('.content'); if (content) content.style.paddingBottom = examMode ? '0px' : '118px';
  }

  function historyRows() { try { return typeof getExamHistory === 'function' ? getExamHistory() : []; } catch (_) { return []; } }
  function diagnosticRecords() { return read('diagnostics', {}); }
  function planProgress() {
    const legacy = safeParse(localStorage.getItem(`s39_daily_plans_${userId()}`) || '', {});
    const day = legacy[todayLocal()] || {};
    const ids = ['diagnostic','practice','errors','mastery','summary'];
    return { done: ids.filter(id => !!day[id]).length, total: ids.length };
  }
  function scoringPrediction() {
    const profile = getProfile(); const records = diagnosticRecords(); const target = profile.targetExam;
    const record = records[target];
    const rows = historyRows().filter(row => target === 'qudrat' ? String(row.exam || '').includes('قدرات') : row.exam === 'تحصيلي').slice(0, 10);
    const values = [];
    if (record && Number.isFinite(Number(record.weightedPercent))) values.push(Number(record.weightedPercent));
    rows.slice().reverse().forEach(row => values.push(Number(row.percent || 0)));
    if (!values.length) return { ready:false, low:0, high:0, center:0, confidence:'ابدأ تحديد المستوى' };
    let center = 0; let weights = 0; values.forEach((value, i) => { const w = i + 1; center += value * w; weights += w; }); center /= weights;
    const times = rows.map(r => Number(r.avgSec || 60)); if (times.length && avg(times) <= 50) center += 1.5; if (times.length && avg(times) > 75) center -= 2;
    const width = values.length >= 8 ? 3 : values.length >= 4 ? 5 : 7; center = Math.round(clamp(center, 0, 100));
    return { ready:true, center, low:Math.round(clamp(center-width,0,100)), high:Math.round(clamp(center+width,0,100)), confidence:width===3?'ثقة مرتفعة':width===5?'ثقة متوسطة':'تقدير أولي' };
  }
  function activityData() { return read('activity', { dates:[], events:[], lastAt:0 }); }
  function markActivity(type) {
    const data = activityData(); const date = todayLocal();
    if (!data.dates.includes(date)) data.dates.push(date);
    data.events.push({ type:type || 'learning', at:Date.now() }); data.events = data.events.slice(-300); data.dates = data.dates.slice(-400); data.lastAt = Date.now(); write('activity', data);
    requestAnimationFrame(() => { const page = activePage(); if (page && page.id === 'homePage') renderHome(); });
  }
  function streakStatus() {
    const data = activityData(); const set = new Set(data.dates || []); const now = new Date(); const today = todayLocal(now); const hasToday = set.has(today);
    let cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate()); if (!hasToday) cursor = new Date(cursor.getTime() - DAY);
    let count = 0; for (let i=0;i<366;i++) { const d=todayLocal(cursor); if(!set.has(d)) break; count++; cursor=new Date(cursor.getTime()-DAY); }
    const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate()+1); const hoursLeft = (midnight.getTime()-now.getTime())/3600000;
    const rescue = Number(getAdminSettings().streak.rescue_window_hours || 6); const risk = !hasToday && count > 0 && hoursLeft <= rescue;
    return { count, hasToday, risk, hoursLeft:Math.max(0, hoursLeft) };
  }
  function avatarHtml(profile, cls) { return `<div class="s47-avatar ${cls || ''}"><img src="${avatarSrc(profile.avatarId)}" alt="${esc(profile.displayName)}"></div>`; }
  function renderHome() {
    const page = document.getElementById('homePage'); if (!page) return;
    const p = getProfile(); const prediction = scoringPrediction(); const plan = planProgress(); const planPct = pct(plan.done, plan.total); const streak = streakStatus();
    const record = diagnosticRecords()[p.targetExam]; const targetScore = record ? Number(record.weightedPercent || 0) : 0;
    const activityText = streak.risk ? `باقي ${Math.max(1,Math.ceil(streak.hoursLeft))} ساعات قبل انقطاع السلسلة` : streak.hasToday ? 'تم تثبيت إنجاز اليوم' : streak.count ? 'أكمل نشاطًا واحدًا اليوم' : 'ابدأ أول يوم في سلسلتك';
    page.innerHTML = `<div class="s47-home">
      <div class="s47-home-head"><div class="s47-user">${avatarHtml(p)}<div><b>هلا ${esc(String(p.displayName || 'يا بطل').split(' ')[0])} 👋</b><span>${targetLabel(p.targetExam)} • المسار ${trackLabel(p.academicTrack)}</span></div></div><div class="s47-head-actions"><button class="s47-streak-pill ${streak.risk?'risk':''}" onclick="s47ShowStreakInfo()"><span class="s47-streak-icon">${streak.risk?'⌛':'🔥'}</span><span>${streak.count}</span></button><button class="s47-icon-btn" onclick="s39EnableReminder&&s39EnableReminder()">${icon('bell')}</button></div></div>
      <section class="s47-hero"><span class="s47-hero-kicker">سهيل رفيق رحلتك</span><h1>${record ? 'نكمل من مستواك الحقيقي' : 'خلّنا نعرف نقطة بدايتك'}</h1><p>${record ? `نتيجتك التشخيصية ${targetScore}%، وخطة اليوم مصممة لتقوية أضعف نقطة عندك.` : 'حدد هل تستهدف القدرات أو التحصيلي، وسهيل يبني لك قياسًا مناسبًا لمسارك العلمي أو الأدبي.'}</p><div class="s47-hero-actions"><button class="main" onclick="${record?"showPage('tasksPage')":"s47OpenDiagnosticChoice()"}">${record?'ابدأ خطة اليوم':'حدد مستواك'}</button><button class="ghost" onclick="showPage('studentSetupPage')">تعديل مساري</button></div></section>
      <div class="s47-kpis"><div class="s47-kpi"><b>${prediction.ready?`${prediction.low}–${prediction.high}`:'—'}</b><span>الدرجة المتوقعة</span></div><div class="s47-kpi"><b>${streak.count} 🔥</b><span>${esc(activityText)}</span></div><div class="s47-kpi"><b>${planPct}%</b><span>خطة اليوم</span></div></div>
      <div class="s47-today"><div class="s47-today-top"><b>رحلة اليوم</b><span>${plan.done}/${plan.total} خطوات</span></div><div class="s47-progress"><i style="width:${planPct}%"></i></div><div class="s47-today-row"><span>${plan.total-plan.done ? `باقي ${plan.total-plan.done} مهام قصيرة` : 'أنجزت خطة اليوم، ممتاز!'}</span><button onclick="showPage('tasksPage')">افتح الخطة</button></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>أين وصلت؟</b><button onclick="showPage('statsPage')">التفاصيل</button></div><div class="s47-path-grid"><button class="s47-path-card" onclick="s47OpenDiagnosticChoice('qudrat')"><div class="icon">∑</div><b>القدرات</b><small>كمي ولفظي وفق مسارك</small><em>${diagnosticRecords().qudrat ? diagnosticRecords().qudrat.weightedPercent+'%' : 'ابدأ'}</em></button><button class="s47-path-card" onclick="s47OpenDiagnosticChoice('tahsili')"><div class="icon">⚛</div><b>التحصيلي</b><small>${p.academicTrack==='literary'?'الأدبي يحتاج بنكًا معتمدًا':'رياضيات وفيزياء وكيمياء والأحياء وعلم البيئة'}</small><em>${diagnosticRecords().tahsili ? diagnosticRecords().tahsili.weightedPercent+'%' : 'ابدأ'}</em></button></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>تحدي مع صديق</b><button onclick="showPage('challengePage')">عرض الكل</button></div><div class="s47-challenge-banner"><div><b>خلّ المذاكرة منافسة ممتعة</b><span>أضف صديقًا بالكود، اختر نوع التحدي، وقارن النتيجة والوقت.</span><button onclick="showPage('challengePage')">ابدأ تحديًا</button></div><div class="s47-challenge-art">🏆</div></div></div>
    </div>`;
    refreshNavigationMode();
  }
  window.s47ShowStreakInfo = function () { const s=streakStatus(); toast(s.risk?`⌛ أكمل سؤالًا أو افتح ملخصًا خلال ${Math.max(1,Math.ceil(s.hoursLeft))} ساعات لحماية السلسلة`:`🔥 سلسلتك ${s.count} يوم. النشاط التعليمي هو الذي يثبت اليوم.`); };

  function renderProfile() {
    const page = document.getElementById('profilePage'); if (!page) return;
    const p = getProfile(); const streak = streakStatus(); const social = getSocial();
    page.innerHTML = `<div class="s47-page">${topbar('حسابي','مسارك وشخصيتك وإعدادات رحلتك',"showPage('homePage')")}
      <div class="s47-profile-hero">${avatarHtml(p)}<div><b>${esc(p.displayName)}</b><p>${targetLabel(p.targetExam)} • المسار ${trackLabel(p.academicTrack)} • ${streak.count} يوم متتالي</p><span class="s47-profile-code">كود الصداقة: ${friendCode()}</span></div></div>
      <div class="s47-section"><div class="s47-setting-list">
        <button class="s47-setting-row" onclick="showPage('studentSetupPage')"><div class="main"><span class="ico">${icon('edit')}</span><div><b>المسار والشخصية</b><small>${targetLabel(p.targetExam)} • ${trackLabel(p.academicTrack)} • اختر من 8 شخصيات</small></div></div><span class="arrow">‹</span></button>
        <button class="s47-setting-row" onclick="showPage('challengePage')"><div class="main"><span class="ico">${icon('challenge')}</span><div><b>الأصدقاء والتحديات</b><small>${social.friends.length} أصدقاء • ${social.challenges.length} تحديات</small></div></div><span class="arrow">‹</span></button>
        <button class="s47-setting-row" onclick="s47OpenDiagnosticChoice()"><div class="main"><span class="ico">◎</span><div><b>إعادة تحديد المستوى</b><small>الاختبار يتغير حسب هدفك ومسارك</small></div></div><span class="arrow">‹</span></button>
        <button class="s47-setting-row" onclick="showPage('savedQuestionsPage')"><div class="main"><span class="ico">♡</span><div><b>الأسئلة المحفوظة</b><small>أسئلتك وملاحظاتك للعودة إليها</small></div></div><span class="arrow">‹</span></button>
      </div></div>
      ${isAdmin()?`<div class="s47-section"><div class="s47-section-head"><b>إدارة سهيل</b></div><div class="s47-setting-list"><button class="s47-setting-row" onclick="showPage('adminSettingsPage')"><div class="main"><span class="ico">${icon('settings')}</span><div><b>الإعدادات العميقة</b><small>التشخيص، الستريك، التحديات، الإشعارات، المحتوى والأداء</small></div></div><span class="arrow">‹</span></button><button class="s47-setting-row" onclick="showPage('questionManagementPage')"><div class="main"><span class="ico">▤</span><div><b>إدارة المحتوى</b><small>الأسئلة والملخصات والمراجعة والنشر</small></div></div><span class="arrow">‹</span></button><button class="s47-setting-row" onclick="showPage('aiGeneratorPage')"><div class="main"><span class="ico">✦</span><div><b>مسودات الذكاء الاصطناعي</b><small>توليد ثم مراجعة قبل الاعتماد</small></div></div><span class="arrow">‹</span></button></div></div>`:''}
      <div class="s47-section"><button class="s47-secondary" style="width:100%" onclick="logoutUser()">تسجيل الخروج</button></div>
    </div>`;
    refreshNavigationMode();
  }

  function renderSetup() {
    const page = ensurePage('studentSetupPage'); const current = getProfile(); if (!setupDraft) setupDraft = { ...current };
    page.innerHTML = `<div class="s47-page">${topbar('إعداد رحلتي','هذه البيانات تغيّر الاختبار وحساب التوقع',"showPage('profilePage')")}
      <div class="s47-card"><div class="s47-field"><label>الاسم الظاهر</label><input class="s47-input" value="${esc(setupDraft.displayName)}" oninput="setupDraft.displayName=this.value"></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>وش هدفك الآن؟</b></div><div class="s47-choice-grid"><button class="s47-choice-card ${setupDraft.targetExam==='qudrat'?'selected':''}" onclick="s47SetupSelect('targetExam','qudrat')"><span class="ico">🎯</span><b>القدرات</b><small>اختبار كمي ولفظي مختلف حسب المسار</small></button><button class="s47-choice-card ${setupDraft.targetExam==='tahsili'?'selected':''}" onclick="s47SetupSelect('targetExam','tahsili')"><span class="ico">⚛</span><b>التحصيلي</b><small>مواد المرحلة الثانوية</small></button></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>مسارك الدراسي</b></div><div class="s47-choice-grid"><button class="s47-choice-card ${setupDraft.academicTrack==='scientific'?'selected':''}" onclick="s47SetupSelect('academicTrack','scientific')"><span class="ico">🧪</span><b>علمي</b><small>توازن كمي ولفظي وتحـصيلي علمي</small></button><button class="s47-choice-card ${setupDraft.academicTrack==='literary'?'selected':''}" onclick="s47SetupSelect('academicTrack','literary')"><span class="ico">📚</span><b>أدبي</b><small>وزن لفظي أعلى في التوقع</small></button></div>${setupDraft.academicTrack==='literary'&&setupDraft.targetExam==='tahsili'?'<div class="s47-page-sub" style="margin-top:8px;color:#b66a19">التحصيلي الأدبي محفوظ في الحساب، لكن قياسه لن يتفعل حتى يضاف بنك أدبي معتمد.</div>':''}</div>
      <div class="s47-section"><div class="s47-section-head"><b>اختر شخصيتك</b><span class="s47-chip">4 ذكور • 4 إناث</span></div><div class="s47-avatar-grid">${avatarItems().map(item=>`<button class="s47-avatar-option ${setupDraft.avatarId===item.id?'selected':''}" onclick="s47SetupSelect('avatarId','${item.id}')"><img src="${avatarSrc(item.id)}" alt="${esc(item.name)}"><span>${esc(item.name)}</span></button>`).join('')}</div></div>
      <button class="s47-primary" style="width:100%;margin-top:16px" onclick="s47SaveSetup()">حفظ وبناء رحلتي</button>
    </div>`;
    refreshNavigationMode();
  }
  window.s47SetupSelect = function (field, value) { setupDraft = { ...(setupDraft || getProfile()), [field]:value }; renderSetup(); };
  window.s47SaveSetup = function () { const p=saveProfile(setupDraft || getProfile()); setupDraft=null; toast('تم حفظ مسارك وشخصيتك'); if (p.targetExam==='tahsili' && p.academicTrack==='literary') showPage('homePage'); else showPage('homePage'); };

  function diagnosticConfig(path, profile) {
    const cfg = getAdminSettings().diagnostic || {};
    if (path === 'qudrat') return profile.academicTrack==='literary' ? (cfg.qudrat_literary || {quant:4,verbal:8}) : (cfg.qudrat_scientific || {quant:6,verbal:6});
    return cfg.tahsili_scientific || {math:3,physics:3,chemistry:3,biology:3};
  }
  function questionPool() { return Array.isArray(window.questions) ? window.questions : (typeof questions !== 'undefined' && Array.isArray(questions) ? questions : []); }
  function chooseQuestions(filter, count, used) {
    const pool = questionPool().filter(filter).filter(q => !used.has(String(q.id || q.question)));
    const marked = pool.filter(q => q.diagnostic); const others = pool.filter(q => !q.diagnostic);
    const candidates = marked.concat(others).sort((a,b)=>hash(String(a.id)+userId())-hash(String(b.id)+userId()));
    return candidates.slice(0,count).map(q=>{used.add(String(q.id || q.question));return q;});
  }
  function buildDiagnostic(path) {
    const p=getProfile(); const cfg=diagnosticConfig(path,p); const used=new Set(); let items=[];
    if(path==='qudrat') {
      items.push(...chooseQuestions(q=>q.exam==='قدرات كمي',Number(cfg.quant||6),used));
      items.push(...chooseQuestions(q=>q.exam==='قدرات لفظي',Number(cfg.verbal||6),used));
    } else {
      const subjectMap=[['رياضيات','math'],['فيزياء','physics'],['كيمياء','chemistry'],['الأحياء وعلم البيئة','biology']];
      subjectMap.forEach(([subject,k])=>items.push(...chooseQuestions(q=>q.exam==='تحصيلي'&&q.subject===subject,Number(cfg[k]||3),used)));
    }
    return items.sort((a,b)=>hash(String(a.id)+'order')-hash(String(b.id)+'order'));
  }
  window.s47OpenDiagnosticChoice = function (preferred) {
    if (!profileExists() && !isAdmin()) { setupDraft=getProfile(); showPage('studentSetupPage'); return; }
    const page=ensurePage('diagnosticChoicePage'); const p=getProfile(); const selected=preferred||p.targetExam;
    page.innerHTML=`<div class="s47-page">${topbar('تحديد المستوى','القياس يتغير حسب هدفك ومسارك',"showPage('homePage')")}
      <div class="s47-diag-start"><h2>مسارك الحالي: ${trackLabel(p.academicTrack)}</h2><p>سهيل لا يعطي جميع الطلاب الاختبار نفسه. توزيع الأسئلة وطريقة حساب التوقع يتغيران حسب المسار والهدف.</p><div class="s47-diag-facts"><div><b>${p.academicTrack==='literary'?'70%':'50%'}</b><span>وزن اللفظي في نموذج القدرات</span></div><div><b>12</b><span>سؤالًا تشخيصيًا</span></div><div><b>≈10د</b><span>مدة متوقعة</span></div></div></div>
      <div class="s47-section"><div class="s47-choice-grid"><button class="s47-choice-card ${selected==='qudrat'?'selected':''}" onclick="s47StartDiagnostic('qudrat')"><span class="ico">🎯</span><b>قياس القدرات</b><small>${p.academicTrack==='literary'?'4 كمي + 8 لفظي':'6 كمي + 6 لفظي'}</small></button><button class="s47-choice-card ${selected==='tahsili'?'selected':''}" onclick="s47StartDiagnostic('tahsili')"><span class="ico">⚛</span><b>قياس التحصيلي</b><small>${p.academicTrack==='literary'?'بانتظار بنك أدبي معتمد':'3 أسئلة من كل مادة'}</small></button></div></div>
      <div class="s47-card" style="margin-top:12px"><b style="font-size:13px">كيف تستخدم النتيجة؟</b><div class="s47-page-sub">تحدد أضعف المهارات، تبني خطة اليوم، وتنتج نطاقًا متوقعًا يتحدث مع كل اختبار جديد. النطاق إرشادي وليس درجة رسمية.</div></div>
      <button class="s47-secondary" style="width:100%;margin-top:10px" onclick="showPage('studentSetupPage')">تعديل الهدف أو المسار</button>
    </div>`;
    activate('diagnosticChoicePage'); refreshNavigationMode();
  };
  window.s47StartDiagnostic = function (path) {
    const p=getProfile(); if(path==='tahsili'&&p.academicTrack==='literary') { toast('التحصيلي الأدبي غير مفعّل حتى إضافة بنك أسئلة معتمد'); return; }
    const items=buildDiagnostic(path); if(!items.length){toast('لا توجد أسئلة كافية لهذا القياس');return;}
    diagnosticState={path,items,index:0,answers:[],selected:null,startedAt:Date.now(),finished:false}; activate('s47DiagnosticPage'); renderDiagnosticQuestion();
  };
  function renderDiagnosticQuestion() {
    const page=ensurePage('s47DiagnosticPage'); const s=diagnosticState; if(!s||!s.items.length)return;
    const q=s.items[s.index]; const choices=Array.isArray(q.choices)?q.choices:[];
    page.innerHTML=`<div class="s47-page no-nav">${topbar('قياس '+targetLabel(s.path),`${s.index+1} من ${s.items.length}`,"s47AbortDiagnostic()")}
      <div class="s47-diag-progress"><i style="width:${pct(s.index,s.items.length)}%"></i></div><div class="s47-question-card"><div class="s47-question-meta"><span class="s47-chip">${esc(q.exam)}</span><span class="s47-chip">${esc(q.subject||q.category||q.skill||'عام')}</span></div><div class="s47-question-text">${esc(q.question)}</div><div class="s47-options">${choices.map((choice,i)=>`<button class="s47-option ${s.selected===i?'selected':''}" onclick="s47SelectDiagnostic(${i})"><i>${['أ','ب','ج','د'][i]||i+1}</i><span>${esc(choice)}</span></button>`).join('')}</div></div>
      <button class="s47-primary s47-diag-next" ${s.selected==null?'disabled':''} onclick="s47NextDiagnostic()">${s.index===s.items.length-1?'عرض النتيجة':'التالي'}</button>
    </div>`;
    refreshNavigationMode();
  }
  window.s47SelectDiagnostic=function(index){if(!diagnosticState)return;diagnosticState.selected=index;renderDiagnosticQuestion();};
  window.s47NextDiagnostic=function(){const s=diagnosticState;if(!s||s.selected==null)return;s.answers.push(s.selected);s.selected=null;if(s.index<s.items.length-1){s.index++;renderDiagnosticQuestion();}else finishDiagnostic();};
  window.s47AbortDiagnostic=function(){if(confirm('هل تريد الخروج من القياس؟ لن تُحفظ الإجابات الحالية.')){diagnosticState=null;showPage('homePage');}};
  function finishDiagnostic() {
    const s=diagnosticState; const p=getProfile(); const groups={}; let correct=0;
    s.items.forEach((q,i)=>{const ok=Number(s.answers[i])===Number(q.correct);if(ok)correct++;const group=s.path==='qudrat'?q.exam:(q.subject||q.category||'تحصيلي');groups[group]||(groups[group]={total:0,correct:0});groups[group].total++;if(ok)groups[group].correct++;});
    Object.values(groups).forEach(g=>g.percent=pct(g.correct,g.total)); let weighted=0;
    if(s.path==='qudrat'){const quant=groups['قدرات كمي']?groups['قدرات كمي'].percent:0;const verbal=groups['قدرات لفظي']?groups['قدرات لفظي'].percent:0;weighted=p.academicTrack==='literary'?quant*.30+verbal*.70:quant*.50+verbal*.50;}
    else weighted=avg(['رياضيات','فيزياء','كيمياء','الأحياء وعلم البيئة'].map(x=>groups[x]?groups[x].percent:0));
    const record={id:Date.now(),path:s.path,academicTrack:p.academicTrack,total:s.items.length,correct,rawPercent:pct(correct,s.items.length),weightedPercent:Math.round(weighted),groups,date:new Date().toISOString(),elapsedSec:Math.round((Date.now()-s.startedAt)/1000)};
    const records=diagnosticRecords();records[s.path]=record;write('diagnostics',records);
    const legacyTracks=s.path==='qudrat'?{'قدرات كمي':groups['قدرات كمي']||{percent:0},'قدرات لفظي':groups['قدرات لفظي']||{percent:0}}:{'تحصيلي':{total:record.total,correct:record.correct,percent:record.weightedPercent}};
    localStorage.setItem(`s39_diagnostic_${userId()}`,JSON.stringify({id:record.id,date:record.date,total:record.total,correct:record.correct,percent:record.weightedPercent,tracks:legacyTracks,weakest:Object.entries(groups).map(([name,g])=>({name,exam:s.path==='qudrat'?name:'تحصيلي',percent:g.percent})).sort((a,b)=>a.percent-b.percent).slice(0,3),elapsed:record.elapsedSec}));
    markActivity('diagnostic');s.finished=true;renderDiagnosticResult(record);
  }
  function renderDiagnosticResult(record) {
    const page=ensurePage('s47DiagnosticPage'); diagnosticState.finished=true;
    const weakest=Object.entries(record.groups).sort((a,b)=>a[1].percent-b[1].percent)[0];
    page.innerHTML=`<div class="s47-page">${topbar('نتيجة تحديد المستوى','هذه نقطة بداية تتحدث مع كل تدريب',"showPage('homePage')")}
      <div class="s47-result-ring" style="--score:${record.weightedPercent}"><div><span>التقدير الداخلي</span><b>${record.weightedPercent}%</b></div></div>
      <div class="s47-result-list">${Object.entries(record.groups).map(([name,g])=>`<div class="s47-result-row"><div class="top"><span>${esc(name)}</span><b>${g.percent}%</b></div><div class="bar"><i style="width:${g.percent}%"></i></div></div>`).join('')}</div>
      <div class="s47-card" style="margin-top:10px"><b style="font-size:14px">أولوية البداية: ${weakest?esc(weakest[0]):'التثبيت'}</b><div class="s47-page-sub">سنزيد مراجعات هذا القسم في خطة اليوم، ثم نعيد تقديرك بعد نتائج فعلية إضافية.</div></div>
      <div class="s47-card" style="margin-top:9px"><b style="font-size:12px">مهم</b><div class="s47-page-sub">${esc(SCORE_CATALOG.disclaimer_ar||'التوقع إرشادي وليس معادلة رسمية.')}</div></div>
      <button class="s47-primary" style="width:100%;margin-top:12px" onclick="showPage('tasksPage')">ابدأ خطة اليوم</button>
    </div>`; refreshNavigationMode();
  }

  function getSocial() { return deepMerge({friends:[],challenges:[],xp:0},read('social',{})); }
  function saveSocial(value) { write('social',value); return value; }
  function renderChallengePage() {
    const page=ensurePage('challengePage'); const p=getProfile(); const social=getSocial(); const templates=Array.isArray(CHALLENGE_CATALOG.templates)?CHALLENGE_CATALOG.templates:[];
    const selfXp=Number(social.xp||0); const ranks=[{name:p.displayName,avatarId:p.avatarId,xp:selfXp,self:true},...social.friends.map(f=>({name:f.name,avatarId:f.avatarId,xp:Number(f.xp||0)}))].sort((a,b)=>b.xp-a.xp);
    page.innerHTML=`<div class="s47-page">${topbar('تحدي الأصدقاء','نافس على الدقة والسرعة بدون تشتيت',"showPage('homePage')")}
      <div class="s47-social-summary"><div><b>${social.friends.length}</b><span>صديق</span></div><div><b>${social.challenges.filter(c=>c.status==='active').length}</b><span>تحدي نشط</span></div><div><b>${selfXp}</b><span>XP</span></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>إضافة صديق</b><span class="s47-chip">كودك ${friendCode()}</span></div><div class="s47-friend-add"><input id="s47FriendInput" class="s47-input" placeholder="كود الصديق أو اسمه"><button class="s47-primary" onclick="s47AddFriend()">إضافة</button></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>الأصدقاء</b></div><div class="s47-friend-list">${social.friends.length?social.friends.map(f=>`<div class="s47-friend">${avatarHtml({avatarId:f.avatarId,displayName:f.name})}<div><b>${esc(f.name)}</b><small>${esc(f.code)} • ${Number(f.xp||0)} XP</small></div><button onclick="s47QuickChallenge('${esc(f.code)}')">تحدي</button></div>`).join(''):'<div class="s47-empty">أضف أول صديق بكود الدعوة، وبعدها يظهر زر التحدي هنا.</div>'}</div></div>
      <div class="s47-section"><div class="s47-section-head"><b>إنشاء تحدٍ</b></div><div class="s47-card"><div class="s47-form-grid"><div class="s47-field"><label>الصديق</label><select id="s47ChallengeFriend" class="s47-select"><option value="">اختر</option>${social.friends.map(f=>`<option value="${esc(f.code)}">${esc(f.name)}</option>`).join('')}</select></div><div class="s47-field"><label>نوع التحدي</label><select id="s47ChallengeTemplate" class="s47-select">${templates.map(t=>`<option value="${esc(t.id)}">${esc(t.title)} • ${t.questions} أسئلة</option>`).join('')}</select></div></div><button class="s47-primary" style="width:100%;margin-top:10px" onclick="s47CreateChallenge()">إرسال التحدي</button></div></div>
      <div class="s47-section"><div class="s47-section-head"><b>التحديات</b></div><div class="s47-challenge-list">${social.challenges.length?social.challenges.slice(0,8).map(c=>`<div class="s47-challenge"><div><b>${esc(c.friendName)} • ${esc(c.title)}</b><small>${c.questions} أسئلة • ينتهي ${new Date(c.expiresAt).toLocaleDateString('ar-SA')}</small></div><span class="s47-status ${c.status}">${c.status==='active'?'نشط':c.status==='done'?'مكتمل':'بانتظار'}</span></div>`).join(''):'<div class="s47-empty">لا توجد تحديات بعد.</div>'}</div></div>
      <div class="s47-section"><div class="s47-section-head"><b>لوحة الأصدقاء</b></div><div class="s47-leaderboard">${ranks.map((r,i)=>`<div class="s47-rank"><strong>${i+1}</strong>${avatarHtml({avatarId:r.avatarId,displayName:r.name})}<div><b>${esc(r.name)} ${r.self?'(أنت)':''}</b><small>${r.xp} نقطة</small></div><em>${i===0?'🏆':'—'}</em></div>`).join('')}</div></div>
    </div>`; refreshNavigationMode();
  }
  window.s47AddFriend=function(){const input=document.getElementById('s47FriendInput');const raw=(input&&input.value||'').trim();if(!raw){toast('اكتب كود الصديق أو اسمه');return;}const social=getSocial();const code=raw.toUpperCase().startsWith('SH-')?raw.toUpperCase():`SH-${String(hash(raw)).slice(-6).padStart(6,'0')}`;if(code===friendCode()){toast('هذا كود حسابك');return;}if(social.friends.some(f=>f.code===code)){toast('الصديق موجود بالفعل');return;}const avatars=avatarItems();const item=avatars[hash(code)%avatars.length];social.friends.push({code,name:raw.toUpperCase().startsWith('SH-')?`صديق ${code.slice(-3)}`:raw,avatarId:item?item.id:'male_01',xp:0,addedAt:Date.now()});saveSocial(social);renderChallengePage();toast('تمت إضافة الصديق محليًا');};
  window.s47QuickChallenge=function(code){renderChallengePage();setTimeout(()=>{const select=document.getElementById('s47ChallengeFriend');if(select)select.value=code;document.getElementById('s47ChallengeTemplate')?.focus();},20);};
  window.s47CreateChallenge=function(){const social=getSocial();const friendCodeValue=document.getElementById('s47ChallengeFriend')?.value||'';const templateId=document.getElementById('s47ChallengeTemplate')?.value||'';const friend=social.friends.find(f=>f.code===friendCodeValue);const template=(CHALLENGE_CATALOG.templates||[]).find(t=>t.id===templateId);if(!friend||!template){toast('اختر الصديق ونوع التحدي');return;}social.challenges.unshift({id:Date.now(),friendCode:friend.code,friendName:friend.name,templateId:template.id,title:template.title,questions:template.questions,status:'active',createdAt:Date.now(),expiresAt:Date.now()+Number(getAdminSettings().challenges.invite_expiry_hours||48)*3600000});saveSocial(social);renderChallengePage();toast('تم إنشاء التحدي');};

  function adminField(path,label,type,options,help) {
    const value=getPath(getAdminSettings(),path); let input='';
    if(type==='select') input=`<select class="s47-select" onchange="s47AdminSet('${path}',this.value,'string')">${(options||[]).map(o=>`<option value="${esc(o.value)}" ${String(value)===String(o.value)?'selected':''}>${esc(o.label)}</option>`).join('')}</select>`;
    else input=`<input class="s47-input" type="${type==='number'?'number':'text'}" value="${esc(value)}" onchange="s47AdminSet('${path}',this.value,'${type}')">`;
    return `<div class="s47-field"><label>${esc(label)}</label>${input}${help?`<div class="s47-page-sub">${esc(help)}</div>`:''}</div>`;
  }
  function adminToggle(path,label,sub) { const on=!!getPath(getAdminSettings(),path); return `<div class="s47-switch-row"><div><b>${esc(label)}</b><small>${esc(sub||'')}</small></div><button class="s47-switch ${on?'on':''}" onclick="s47AdminToggle('${path}')" aria-label="${esc(label)}"></button></div>`; }
  function adminTabs() { const tabs=[['overview','نظرة عامة'],['general','عام'],['learning','التعلم والتشخيص'],['motivation','الستريك والتحديات'],['notify','الإشعارات والميزات'],['content','المحتوى والأداء'],['backup','نسخ واستعادة']]; return `<div class="s47-admin-tabs">${tabs.map(([id,label])=>`<button class="s47-admin-tab ${adminTab===id?'active':''}" onclick="s47AdminTab('${id}')">${label}</button>`).join('')}</div>`; }
  function renderAdminBody() {
    const s=getAdminSettings(); const bank=questionPool().length; const summariesCount=typeof smartSummaries!=='undefined'&&Array.isArray(smartSummaries)?smartSummaries.length:0;
    if(adminTab==='overview') return `<div class="s47-admin-hero"><h2>لوحة تحكم سهيل</h2><p>إعدادات مركزية للرحلة التعليمية، القياس، التحفيز، المحتوى والأداء. إعدادات هذه النسخة تحفظ محليًا، مع ملفات إعداد جاهزة للربط بالـ API.</p><div class="s47-admin-kpis"><div><b>${bank}</b><span>سؤال</span></div><div><b>${summariesCount}</b><span>ملخص</span></div><div><b>${avatarItems().length}</b><span>شخصيات</span></div><div><b>47</b><span>آخر سبرنت</span></div></div></div><div class="s47-section"><div class="s47-admin-group"><h3>حالة المزايا</h3><p>تحقق سريع قبل أي إطلاق تجريبي.</p>${adminToggle('features.summaries','الملخصات','عرض بوابة الملخصات')}${adminToggle('features.challenges','تحديات الأصدقاء','إنشاء ومتابعة التحديات')}${adminToggle('learning.enable_prediction','توقع الدرجة','نطاق إرشادي حسب الأداء')}${adminToggle('content.require_reviewer_approval','اعتماد المراجع','منع النشر المباشر')}</div></div>`;
    if(adminTab==='general') return `<div class="s47-admin-group"><h3>هوية وتشغيل التطبيق</h3><p>القيم العامة التي تظهر في تجربة الطالب.</p>${adminField('general.app_name','اسم التطبيق','text')}${adminField('general.tagline','العبارة','text')}<div class="s47-form-grid">${adminField('general.splash_seconds','مدة الافتتاحية بالثواني','number')}${adminField('general.default_language','اللغة الافتراضية','select',[{value:'ar',label:'العربية'}])}</div>${adminToggle('general.maintenance_mode','وضع الصيانة','تعطيل دخول الطلاب مؤقتًا')}${adminField('general.support_email','بريد الدعم','text')}</div>`;
    if(adminTab==='learning') return `<div class="s47-admin-group"><h3>الخطة اليومية</h3><p>المستهدفات الافتراضية التي يبني عليها سهيل رحلة اليوم.</p><div class="s47-form-grid">${adminField('learning.daily_question_goal','هدف الأسئلة','number')}${adminField('learning.daily_error_goal','هدف مراجعة الأخطاء','number')}${adminField('learning.daily_summary_goal','هدف الملخصات','number')}${adminField('learning.default_session_minutes','دقائق الجلسة','number')}</div>${adminToggle('learning.enable_prediction','توقع الدرجة','إظهار نطاق التوقع للطالب')}</div><div class="s47-admin-group"><h3>اختبار تحديد المستوى</h3><p>توزيع مستقل للعلمي والأدبي.</p><div class="s47-form-grid">${adminField('diagnostic.qudrat_scientific.quant','كمي علمي','number')}${adminField('diagnostic.qudrat_scientific.verbal','لفظي علمي','number')}${adminField('diagnostic.qudrat_literary.quant','كمي أدبي','number')}${adminField('diagnostic.qudrat_literary.verbal','لفظي أدبي','number')}</div>${adminToggle('diagnostic.separate_records','فصل سجلات القياس','القدرات والتحصيلي لا يختلطان')}${adminField('diagnostic.allow_retake_after_days','إعادة القياس بعد أيام','number')}</div>`;
    if(adminTab==='motivation') return `<div class="s47-admin-group"><h3>السلسلة اليومية</h3><p>لا يحسب فتح التطبيق وحده؛ يجب نشاط تعليمي.</p>${adminToggle('streak.enabled','تفعيل الستريك','إظهار علامة النار')}${adminField('streak.rescue_window_hours','نافذة الساعة الرملية','number',null,'تظهر قبل نهاية اليوم بهذا العدد من الساعات')}${adminToggle('streak.freeze_tokens_enabled','رموز تجميد الستريك','ميزة مستقبلية')}</div><div class="s47-admin-group"><h3>التحديات</h3><p>حدود وأزمنة المنافسة بين الطلاب.</p>${adminToggle('challenges.enabled','تفعيل التحديات','إظهار صفحة الصداقة والمنافسة')}<div class="s47-form-grid">${adminField('challenges.friend_limit','حد الأصدقاء','number')}${adminField('challenges.invite_expiry_hours','صلاحية الدعوة بالساعات','number')}${adminField('challenges.daily_question_count','أسئلة التحدي اليومي','number')}${adminField('challenges.weekly_question_count','أسئلة التحدي الأسبوعي','number')}</div>${adminToggle('challenges.allow_rematch','إعادة التحدي','السماح بمباراة جديدة')}</div>`;
    if(adminTab==='notify') return `<div class="s47-admin-group"><h3>الإشعارات</h3><p>الواجهة جاهزة، أما الإشعارات بعد إغلاق التطبيق فتحتاج Expo/APNs لاحقًا.</p>${adminToggle('notifications.enabled','الإشعارات','المفتاح الرئيسي')}${adminToggle('notifications.daily_plan','خطة اليوم','تذكير يومي بالخطة')}${adminToggle('notifications.streak_warning','تحذير الستريك','تنبيه نافذة الساعة الرملية')}${adminToggle('notifications.challenge_invites','دعوات التحدي','تنبيه عند دعوة صديق')}${adminToggle('notifications.review_due','المراجعات المستحقة','قوانين وأخطاء مستحقة')}<div class="s47-form-grid">${adminField('notifications.quiet_hours_start','بداية الهدوء','text')}${adminField('notifications.quiet_hours_end','نهاية الهدوء','text')}</div></div><div class="s47-admin-group"><h3>مفاتيح المزايا</h3>${adminToggle('features.friends','الأصدقاء','إضافة وإدارة الأصدقاء')}${adminToggle('features.xp','نقاط XP','نظام التحفيز')}${adminToggle('features.ai_drafts','مسودات AI','مولد الأدمن')}${adminToggle('features.ads','الإعلانات','المساحة الإعلانية')}${adminToggle('features.tahsili_common_for_all','تحصيلي موحد','لا يتغير بمسار القدرات')}</div>`;
    if(adminTab==='content') return `<div class="s47-admin-group"><h3>حوكمة المحتوى</h3><p>قواعد الجودة قبل الاعتماد والنشر.</p>${adminToggle('content.require_reviewer_approval','اعتماد المراجع','كل محتوى يمر بالمراجعة')}${adminToggle('content.require_explanation','الشرح إلزامي','رفض السؤال بدون شرح')}${adminToggle('content.require_skill_tag','المهارة إلزامية','ربط السؤال بالتحليل والخطة')}${adminToggle('content.require_source','المصدر إلزامي','توثيق مرجع السؤال')}${adminField('content.duplicate_threshold','حد التشابه','number',null,'القيمة الافتراضية 0.8')}</div><div class="s47-admin-group"><h3>الأداء</h3><p>ضبط حجم البيانات المحملة في كل طلب.</p>${adminToggle('performance.prefer_webp','صور WebP','استخدام الأصول المضغوطة')}${adminToggle('performance.preload_next_question','تحميل السؤال التالي','تحسين سرعة الانتقال')}<div class="s47-form-grid">${adminField('performance.question_page_size','حجم صفحة الأسئلة','number')}${adminField('performance.summary_page_size','حجم صفحة الملخصات','number')}${adminField('performance.client_cache_minutes','كاش العميل بالدقائق','number')}</div></div>`;
    const json=JSON.stringify(s,null,2); return `<div class="s47-admin-group"><h3>تصدير الإعدادات</h3><p>احتفظ بنسخة قبل أي تعديل كبير.</p><textarea id="s47AdminJson" class="s47-textarea s47-admin-json">${esc(json)}</textarea><div class="s47-admin-actions"><button class="s47-primary" onclick="s47AdminCopy()">نسخ JSON</button><button class="s47-secondary" onclick="s47AdminImport()">استيراد النص</button><button class="s47-secondary" onclick="s47AdminReset()">استعادة الافتراضي</button><button class="s47-secondary" onclick="s47AdminDownload()">تنزيل ملف</button></div></div>`;
  }
  function renderAdmin() {
    const page=ensurePage('adminSettingsPage'); if(!isAdmin()){showPage('homePage');return;}
    page.innerHTML=`<div class="s47-page">${topbar('إعدادات الأدمن','تحكم عميق من مكان واحد',"showPage('profilePage')")}${adminTabs()}${renderAdminBody()}</div>`; refreshNavigationMode();
  }
  window.s47AdminTab=function(tab){adminTab=tab;renderAdmin();};
  window.s47AdminSet=function(path,value,type){const s=getAdminSettings();let parsed=value;if(type==='number')parsed=Number(value);if(type==='boolean')parsed=value==='true';setPath(s,path,parsed);saveAdminSettings(s);toast('تم حفظ الإعداد');};
  window.s47AdminToggle=function(path){const s=getAdminSettings();setPath(s,path,!getPath(s,path));saveAdminSettings(s);renderAdmin();};
  window.s47AdminCopy=async function(){const text=document.getElementById('s47AdminJson')?.value||'';try{await navigator.clipboard.writeText(text);toast('تم نسخ الإعدادات');}catch(_){toast('حدد النص وانسخه يدويًا');}};
  window.s47AdminImport=function(){const area=document.getElementById('s47AdminJson');try{const parsed=JSON.parse(area.value);saveAdminSettings(deepMerge(deepClone(DEFAULT_ADMIN),parsed));renderAdmin();toast('تم استيراد الإعدادات');}catch(_){toast('JSON غير صالح');}};
  window.s47AdminReset=function(){if(confirm('استعادة جميع الإعدادات الافتراضية؟')){localStorage.removeItem('s47_admin_settings');renderAdmin();toast('تمت الاستعادة');}};
  window.s47AdminDownload=function(){const blob=new Blob([JSON.stringify(getAdminSettings(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='suhail_admin_settings.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500);};

  function patchActivityHooks() {
    if (!window.__s47AnswerPatched && typeof window.answerQuiz === 'function') { window.__s47AnswerPatched=true; const old=window.answerQuiz; window.answerQuiz=function(){const r=old.apply(this,arguments);markActivity('answer');return r;}; }
    if (!window.__s47SummaryPatched && typeof window.openSummaryUnit === 'function') { window.__s47SummaryPatched=true; const old=window.openSummaryUnit; window.openSummaryUnit=function(){const r=old.apply(this,arguments);markActivity('summary');setTimeout(refreshNavigationMode,40);return r;}; }
    if (!window.__s47FinishPatched && typeof window.finishExam === 'function') { window.__s47FinishPatched=true; const old=window.finishExam; window.finishExam=function(){const r=old.apply(this,arguments);markActivity('exam');const social=getSocial();social.xp=Number(social.xp||0)+Math.max(10,((typeof activeQuestions!=='undefined'&&activeQuestions.length)||5)*2);saveSocial(social);return r;}; }
  }
  function patchLogin() {
    if(window.__s47LoginPatched||typeof window.loginUser!=='function')return;window.__s47LoginPatched=true;const old=window.loginUser;window.loginUser=function(){const before=session();const r=old.apply(this,arguments);setTimeout(()=>{const after=session();if(after&&!before&&after.role==='student'&&!profileExists()){setupDraft=defaultProfile();showPage('studentSetupPage');}else if(after)renderHome();},100);return r;};
  }
  function patchShowPage() {
    if(window.__s47ShowPatched)return;window.__s47ShowPatched=true;const old=window.showPage;
    window.showPage=function(id){
      if(id==='accountPage')id='profilePage';if(id==='friendsPage')id='challengePage';
      if(id==='studentSetupPage'){activate(id);renderSetup();return;}
      if(id==='diagnosticChoicePage'){activate(id);window.s47OpenDiagnosticChoice();return;}
      if(id==='s47DiagnosticPage'){activate(id);diagnosticState&&diagnosticState.finished?null:renderDiagnosticQuestion();return;}
      if(id==='challengePage'){activate(id);renderChallengePage();return;}
      if(id==='adminSettingsPage'){if(!isAdmin()){toast('هذه الصفحة للأدمن فقط');return;}activate(id);renderAdmin();return;}
      const result=typeof old==='function'?old.apply(this,[id]):activate(id);
      setTimeout(()=>{if(id==='homePage')renderHome();else if(id==='profilePage')renderProfile();refreshNavigationMode();},45);return result;
    };
  }
  function patchExistingLinks() { window.s39OpenDiagnostic=window.s47OpenDiagnosticChoice; }
  function installObserver() {
    const content=document.querySelector('.content');if(!content||window.__s47Observer)return;window.__s47Observer=true;
    const observer=new MutationObserver(()=>{clearTimeout(navObserverTimer);navObserverTimer=setTimeout(refreshNavigationMode,30);});observer.observe(content,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  }
  function install() {
    document.body.classList.add('s47-ready'); ['studentSetupPage','diagnosticChoicePage','s47DiagnosticPage','challengePage','adminSettingsPage'].forEach(ensurePage);
    ensureNavigation(); patchShowPage(); patchExistingLinks(); patchActivityHooks(); patchLogin(); installObserver();
    const active=activePage(); if(active&&active.id==='homePage')renderHome(); else if(active&&active.id==='profilePage')renderProfile();
    refreshNavigationMode(); window.SUHAIL_RELEASE=VERSION;
    setTimeout(()=>{patchActivityHooks();patchExistingLinks();refreshNavigationMode();},500);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install();
})();
