/* Suhail Sprints 30-39: unified learning journey */
(function () {
  'use strict';
  const VERSION = '39.0.0';
  const DAY = 86400000;
  const MAIN_PAGES = new Set(['homePage', 'summariesPage', 'reviewPage', 'tasksPage', 'profilePage']);
  const BRANCH_PAGES = new Set(['diagnosticPage', 'errorReviewPage', 'skillHubPage', 'statsPage']);
  const REASONS = ['فهم الفكرة', 'اختيار القانون', 'تسرع', 'إدارة الوقت', 'قراءة السؤال'];
  const INTERVALS = [1, 3, 7, 14, 30];
  let diagnosticState = null;
  let errorFilter = 'due';
  let skillHubState = null;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[ch]));
  }
  function safeParse(raw, fallback) {
    try { return JSON.parse(raw); } catch (_) { return fallback; }
  }
  function userKey() {
    try { return typeof getUserKey === 'function' ? getUserKey() : 'guest'; } catch (_) { return 'guest'; }
  }
  function key(name) { return `s39_${name}_${userKey()}`; }
  function read(name, fallback) { return safeParse(localStorage.getItem(key(name)) || '', fallback); }
  function write(name, value) { localStorage.setItem(key(name), JSON.stringify(value)); }
  function today() { return new Date().toISOString().slice(0, 10); }
  function pct(a, b) { return b ? Math.round((a / b) * 100) : 0; }
  function avg(values) { return values.length ? values.reduce((a, b) => a + Number(b || 0), 0) / values.length : 0; }
  function clamp(n, min, max) { return Math.max(min, Math.min(max, Number(n || 0))); }
  function shuffle(items) {
    const out = items.slice();
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }
  function authName() {
    try {
      const session = typeof getAuthSession === 'function' ? getAuthSession() : null;
      return (session && session.name) ? String(session.name).split(' ')[0] : 'يا بطل';
    } catch (_) { return 'يا بطل'; }
  }
  function backSvg() {
    return '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M11 6l10 10-10 10"/></svg>';
  }
  function header(title, subtitle, action) {
    return `<div class="s39-header"><button class="s39-back" onclick="${action || "showPage('homePage')"}" aria-label="العودة">${backSvg()}</button><div class="s39-formula f1">a²+b²=c²</div><div class="s39-formula f2">E=mc²</div><div class="s39-header-copy"><div class="s39-header-title">${esc(title)}</div>${subtitle ? `<div class="s39-header-sub">${esc(subtitle)}</div>` : ''}</div></div>`;
  }
  function nav(active) {
    const item = (id, label, icon, action) => `<button class="s39-nav-item ${active === id ? 'active' : ''}" onclick="${action}"><span>${icon}</span><small>${label}</small></button>`;
    return `<div class="s39-main-nav">
      ${item('review', 'المراجعة', '↻', "showPage('reviewPage')")}
      ${item('summaries', 'الملخصات', '▤', "s28SummariesGateway()")}
      ${item('home', 'الرئيسية', '⌂', "showPage('homePage')")}
      ${item('tasks', 'المهام', '✓', "showPage('tasksPage')")}
      ${item('profile', 'الحساب', '◉', "showPage('profilePage')")}
    </div>`;
  }
  function ensurePage(id) {
    let page = document.getElementById(id);
    if (!page) {
      page = document.createElement('div');
      page.id = id;
      page.className = 'page';
      const content = document.querySelector('.content');
      if (content) content.appendChild(page);
    }
    return page;
  }
  function setPageMode(id) {
    document.body.classList.remove('s39-force-main', 's39-force-branch', 's39-force-exam', 's28-nav-open');
    if (MAIN_PAGES.has(id)) document.body.classList.add('s39-force-main');
    else if (BRANCH_PAGES.has(id)) document.body.classList.add('s39-force-branch');
    if (id === 'exercisePage' && examRunning()) document.body.classList.add('s39-force-exam');
  }
  function examRunning() {
    try { return typeof isExamInProgress === 'function' && isExamInProgress(); } catch (_) { return false; }
  }
  function history() {
    try { return typeof getExamHistory === 'function' ? getExamHistory() : []; } catch (_) { return []; }
  }
  function diagnosticRecord() { return read('diagnostic', null); }
  function trackStats(exam) {
    const rows = history().filter(x => x.exam === exam).slice(0, 8);
    const diag = diagnosticRecord();
    const diagTrack = diag && diag.tracks ? diag.tracks[exam] : null;
    const values = rows.map(x => Number(x.percent || 0));
    if (diagTrack) values.push(Number(diagTrack.percent || 0));
    return {
      attempts: rows.length,
      percent: values.length ? Math.round(avg(values)) : 0,
      last: rows[0] ? Number(rows[0].percent || 0) : (diagTrack ? diagTrack.percent : 0),
      avgSec: rows.length ? Math.round(avg(rows.map(x => x.avgSec || 60))) : 0
    };
  }
  function prediction() {
    const rows = history().slice(0, 12);
    const diag = diagnosticRecord();
    const diagScore = diag ? Number(diag.percent || 0) : null;
    let weighted = 0, weights = 0;
    rows.forEach((row, i) => {
      const w = Math.max(1, 12 - i);
      weighted += Number(row.percent || 0) * w;
      weights += w;
    });
    const historyScore = weights ? weighted / weights : null;
    let center = diagScore != null && historyScore != null ? (diagScore * 0.35 + historyScore * 0.65) : (historyScore != null ? historyScore : diagScore);
    if (center == null) return { ready: false, low: 0, high: 0, center: 0, confidence: 'ابدأ التشخيص' };
    const recentTimes = rows.slice(0, 5).map(x => Number(x.avgSec || 60));
    if (recentTimes.length && avg(recentTimes) <= 50) center += 1.5;
    if (recentTimes.length && avg(recentTimes) > 75) center -= 2;
    const attempts = rows.length + (diag ? 1 : 0);
    const width = attempts >= 8 ? 3 : attempts >= 4 ? 5 : 7;
    center = Math.round(clamp(center, 0, 100));
    return {
      ready: true,
      center,
      low: Math.round(clamp(center - width, 0, 100)),
      high: Math.round(clamp(center + width, 0, 100)),
      confidence: attempts >= 8 ? 'ثقة مرتفعة' : attempts >= 4 ? 'ثقة متوسطة' : 'تقدير أولي'
    };
  }
  function errors() { return read('errors', []); }
  function saveErrors(items) { write('errors', items.slice(0, 500)); }
  function dueErrors() {
    const now = Date.now();
    return errors().filter(x => !x.mastered || Number(x.dueAt || 0) <= now);
  }
  function masterySchedule() { return read('mastery_schedule', {}); }
  function saveMasterySchedule(value) { write('mastery_schedule', value); }
  function masteryLabel(rawKey) {
    const parts = String(rawKey || '').split('::');
    if (parts.length >= 4) return { type: parts[0] === 'law' ? 'قانون' : 'تعريف', title: parts.slice(3).join(' '), unit: parts[2], stage: parts[1] };
    return { type: String(rawKey).startsWith('law') ? 'قانون' : 'تعريف', title: String(rawKey).replace(/^def_\d+_/, '').replace(/_/g, ' '), unit: '', stage: '' };
  }
  function syncMasterySchedule() {
    const raw = safeParse(localStorage.getItem('suhail_mastery_v1') || '{}', {});
    const schedule = masterySchedule();
    let changed = false;
    Object.entries(raw).forEach(([itemKey, status]) => {
      if (!schedule[itemKey]) {
        schedule[itemKey] = {
          key: itemKey,
          status,
          repetition: status === 'mastered' ? 1 : 0,
          dueAt: Date.now() + (status === 'mastered' ? 3 : 0) * DAY,
          updatedAt: Date.now()
        };
        changed = true;
      } else if (schedule[itemKey].status !== status) {
        schedule[itemKey].status = status;
        schedule[itemKey].dueAt = status === 'review' ? Date.now() : schedule[itemKey].dueAt;
        schedule[itemKey].updatedAt = Date.now();
        changed = true;
      }
    });
    if (changed) saveMasterySchedule(schedule);
    return schedule;
  }
  function dueMastery() {
    const now = Date.now();
    return Object.values(syncMasterySchedule()).filter(x => x.status === 'review' || Number(x.dueAt || 0) <= now);
  }
  function visits() { return read('visits', []); }
  function updateVisit() {
    const dates = visits();
    const t = today();
    if (!dates.includes(t)) {
      dates.push(t);
      write('visits', dates.slice(-120));
    }
  }
  function streak() {
    const set = new Set(visits());
    let cursor = new Date();
    let count = 0;
    for (let i = 0; i < 366; i++) {
      const d = cursor.toISOString().slice(0, 10);
      if (!set.has(d)) {
        if (i === 0) { cursor = new Date(cursor.getTime() - DAY); continue; }
        break;
      }
      count++;
      cursor = new Date(cursor.getTime() - DAY);
    }
    return count;
  }
  function weakestTrack() {
    const exams = ['قدرات كمي', 'قدرات لفظي', 'تحصيلي'];
    const stats = exams.map(exam => ({ exam, ...trackStats(exam) }));
    return stats.sort((a, b) => (a.percent || 0) - (b.percent || 0))[0];
  }
  function planState() {
    const all = read('daily_plans', {});
    return { all, today: all[today()] || {} };
  }
  function setTaskDone(taskId, done) {
    const state = planState();
    state.all[today()] = { ...state.today, [taskId]: done };
    write('daily_plans', state.all);
    const active = document.querySelector('.page.active');
    if (active && active.id === 'tasksPage') renderTasksPage();
    if (active && active.id === 'homePage') renderJourneyHome();
  }
  function dailyTasks() {
    const diag = diagnosticRecord();
    const weak = weakestTrack();
    const dueE = dueErrors().length;
    const dueM = dueMastery().length;
    const tasks = [];
    if (!diag) tasks.push({ id: 'diagnostic', icon: '◎', title: 'اختبار تشخيصي', detail: '15 سؤالًا تقيس الكمي واللفظي والتحصيلي', action: 's39OpenDiagnostic()' });
    tasks.push({ id: 'practice', icon: '✦', title: `تدريب ${weak.exam}`, detail: '10 أسئلة مركزة على المسار الأقل أداءً', action: `s39StartFocusedPractice('${esc(weak.exam)}')` });
    tasks.push({ id: 'errors', icon: '↻', title: 'مراجعة الأخطاء', detail: dueE ? `${dueE} أخطاء مستحقة للمراجعة` : 'راجع آخر خطأ وثبّت السبب الصحيح', action: 's39OpenErrors()' });
    tasks.push({ id: 'summary', icon: '▤', title: 'ملخص واحد', detail: 'اقرأ بطاقة واحدة ثم علّمها كمنجزة', action: "s28SummariesGateway()" });
    if (dueM) tasks.push({ id: 'mastery', icon: '✓', title: 'تثبيت الإتقان', detail: `${dueM} تعريفات أو قوانين موعدها اليوم`, action: "showPage('tasksPage')" });
    return tasks.slice(0, 5);
  }
  function planProgress() {
    const tasks = dailyTasks();
    const done = planState().today;
    return { done: tasks.filter(t => done[t.id]).length, total: tasks.length };
  }
  function companionMessage() {
    const hour = new Date().getHours();
    const p = prediction();
    const due = dueErrors().length + dueMastery().length;
    if (!diagnosticRecord()) return 'خلّنا نبدأ بقياس بسيط، وبعدها أبني لك الطريق المناسب.';
    if (due > 0) return `عندك ${due} مراجعات قصيرة اليوم. إنهاؤها أهم من زيادة عدد الأسئلة.`;
    if (hour < 12) return 'صباح الإنجاز! جلسة قصيرة الآن تريحك بقية اليوم.';
    if (hour < 18) return p.ready ? `مستواك المتوقع ${p.low}–${p.high}. خطوة اليوم ترفع الثبات.` : 'ابدأ جلسة اليوم، وسأحوّل نتيجتك إلى خطة واضحة.';
    return 'لا تحتاج جلسة طويلة؛ عشر دقائق تحافظ على سلسلتك.';
  }

  function renderJourneyHome() {
    const page = document.getElementById('homePage');
    if (!page) return;
    updateVisit();
    syncMasterySchedule();
    const p = prediction();
    const plan = planProgress();
    const planPercent = pct(plan.done, plan.total);
    const tracks = ['قدرات كمي', 'قدرات لفظي', 'تحصيلي'].map(exam => ({ exam, ...trackStats(exam) }));
    const diag = diagnosticRecord();
    const bankCount = Array.isArray(questions) ? questions.length : 0;
    page.innerHTML = `<div class="s39-home">
      <div class="s39-home-top"><div><div class="s39-hello">مرحبًا ${esc(authName())} 👋</div><div class="s39-date">${new Date().toLocaleDateString('ar-SA', { weekday: 'long', day: 'numeric', month: 'long' })}</div></div><button class="s39-bell" onclick="s39EnableReminder()" aria-label="التذكيرات">◔</button></div>
      <div class="s39-companion"><div class="s39-companion-mark">س</div><div><div class="s39-companion-title">سهيل معك اليوم</div><div class="s39-companion-text">${esc(companionMessage())}</div></div></div>
      ${!diag ? `<div class="s39-diagnostic-call"><div><b>ابدأ من مكانك الحقيقي</b><span>اختبار قصير، ثم خطة ودرجة متوقعة.</span></div><button onclick="s39OpenDiagnostic()">ابدأ التشخيص</button></div>` : ''}
      <div class="s39-score-row">
        <div class="s39-score-card prediction"><span>درجتك المتوقعة</span><b>${p.ready ? `${p.low}–${p.high}` : '—'}</b><small>${esc(p.confidence)}</small></div>
        <div class="s39-score-card"><span>التزامك</span><b>${streak()}</b><small>يوم متتالي</small></div>
        <div class="s39-score-card"><span>خطة اليوم</span><b>${planPercent}%</b><small>${plan.done}/${plan.total} مهام</small></div>
      </div>
      <button class="s39-daily-cta" onclick="showPage('tasksPage')"><span><b>ابدأ رحلة اليوم</b><small>${plan.total - plan.done} خطوات متبقية • نحو 20 دقيقة</small></span><i>←</i></button>
      <div class="s39-section-head"><b>أين وصلت؟</b><button onclick="showPage('statsPage')">التفاصيل</button></div>
      <div class="s39-tracks">${tracks.map(t => `<div class="s39-track"><div class="s39-track-top"><b>${esc(t.exam)}</b><span>${t.percent || 0}%</span></div><div class="s39-progress"><i style="width:${t.percent || 0}%"></i></div><small>${t.attempts ? `${t.attempts} اختبارات • آخر نتيجة ${t.last}%` : 'بانتظار أول قياس'}</small></div>`).join('')}</div>
      <div class="s39-insight-grid"><button onclick="s39OpenErrors()"><b>${dueErrors().length}</b><span>أخطاء للمراجعة</span></button><button onclick="showPage('reviewPage')"><b>${dueMastery().length}</b><span>مراجعات إتقان</span></button><button onclick="s28SummariesGateway()"><b>${Array.isArray(smartSummaries) ? smartSummaries.length : 0}</b><span>بطاقات ملخص</span></button><button onclick="s39OpenQuestionBank()"><b>${bankCount}</b><span>سؤال منظم</span></button></div>
      <div class="s39-prediction-note">التوقع نطاق إرشادي يتحدث مع نتائجك وسرعتك وثباتك، وليس ضمانًا للدرجة الرسمية.</div>
      ${nav('home')}
    </div>`;
    setPageMode('homePage');
  }

  function diagnosticItems() {
    const exams = ['قدرات كمي', 'قدرات لفظي', 'تحصيلي'];
    const out = [];
    exams.forEach(exam => {
      const marked = questions.filter(q => q.exam === exam && q.diagnostic).slice(0, 5);
      const fallback = questions.filter(q => q.exam === exam).slice(0, 5);
      out.push(...(marked.length === 5 ? marked : fallback));
    });
    return out;
  }
  window.s39OpenDiagnostic = function () {
    diagnosticState = { items: diagnosticItems(), index: 0, answers: [], startedAt: Date.now(), selected: null };
    activatePage('diagnosticPage');
    setPageMode('diagnosticPage');
    renderDiagnostic();
  };
  function renderDiagnostic() {
    const page = ensurePage('diagnosticPage');
    const state = diagnosticState;
    if (!state || !state.items.length) {
      page.innerHTML = `<div class="s39-page">${header('الاختبار التشخيصي', '', "showPage('homePage')")}<div class="s39-empty">لا توجد أسئلة تشخيصية.</div></div>`;
      return;
    }
    const q = state.items[state.index];
    const choices = Array.isArray(q.choices) ? q.choices : (q.options || []);
    page.innerHTML = `<div class="s39-page s39-diagnostic-page">${header('قياس البداية', `${state.index + 1} من ${state.items.length}`, "showPage('homePage')")}
      <div class="s39-diag-progress"><i style="width:${pct(state.index, state.items.length)}%"></i></div>
      <div class="s39-diag-meta"><span>${esc(q.exam)}</span><span>${esc(q.category || q.skill)}</span></div>
      <div class="s39-question">${esc(q.question)}</div>
      <div class="s39-options">${choices.map((c, i) => `<button class="${state.selected === i ? 'selected' : ''}" onclick="s39ChooseDiagnostic(${i})"><span>${['أ', 'ب', 'ج', 'د'][i] || i + 1}</span>${esc(c)}</button>`).join('')}</div>
      <button class="s39-next" ${state.selected == null ? 'disabled' : ''} onclick="s39NextDiagnostic()">${state.index === state.items.length - 1 ? 'عرض النتيجة' : 'التالي'}</button>
    </div>`;
  }
  window.s39ChooseDiagnostic = function (index) { diagnosticState.selected = index; renderDiagnostic(); };
  window.s39NextDiagnostic = function () {
    if (!diagnosticState || diagnosticState.selected == null) return;
    diagnosticState.answers.push(diagnosticState.selected);
    diagnosticState.selected = null;
    if (diagnosticState.index < diagnosticState.items.length - 1) {
      diagnosticState.index++;
      renderDiagnostic();
    } else finishDiagnostic();
  };
  function finishDiagnostic() {
    const state = diagnosticState;
    const tracks = {};
    const skills = {};
    let correct = 0;
    state.items.forEach((q, i) => {
      const ok = Number(state.answers[i]) === Number(q.correct);
      if (ok) correct++;
      tracks[q.exam] ||= { total: 0, correct: 0 };
      tracks[q.exam].total++;
      if (ok) tracks[q.exam].correct++;
      const skill = q.skill || q.category || 'عام';
      skills[skill] ||= { total: 0, correct: 0, exam: q.exam };
      skills[skill].total++;
      if (ok) skills[skill].correct++;
    });
    Object.values(tracks).forEach(x => x.percent = pct(x.correct, x.total));
    const skillRows = Object.entries(skills).map(([name, x]) => ({ name, ...x, percent: pct(x.correct, x.total) })).sort((a, b) => a.percent - b.percent);
    const record = {
      id: Date.now(), date: new Date().toISOString(), total: state.items.length, correct,
      percent: pct(correct, state.items.length), tracks, weakest: skillRows.slice(0, 3),
      elapsed: Math.round((Date.now() - state.startedAt) / 1000)
    };
    write('diagnostic', record);
    setTaskDone('diagnostic', true);
    const page = ensurePage('diagnosticPage');
    const p = prediction();
    page.innerHTML = `<div class="s39-page">${header('نتيجة القياس', 'هذه نقطة البداية وليست حكمًا نهائيًا', "showPage('homePage')")}
      <div class="s39-result-hero"><small>مستواك الحالي</small><b>${record.percent}%</b><span>${record.correct} من ${record.total}</span></div>
      <div class="s39-result-tracks">${Object.entries(record.tracks).map(([exam, x]) => `<div><span>${esc(exam)}</span><b>${x.percent}%</b><i><em style="width:${x.percent}%"></em></i></div>`).join('')}</div>
      <div class="s39-result-pred"><span>توقع سهيل الأولي</span><b>${p.low}–${p.high}</b><small>يتحسن بعد كل اختبار جديد</small></div>
      <div class="s39-section-head"><b>ابدأ بهذه الأولويات</b></div>
      <div class="s39-priorities">${record.weakest.map((x, i) => `<div><strong>${i + 1}</strong><span><b>${esc(x.name)}</b><small>${esc(x.exam)} • ${x.percent}%</small></span></div>`).join('')}</div>
      <button class="s39-next" onclick="showPage('tasksPage')">افتح خطة اليوم</button>
    </div>`;
  }

  function reasonBreakdown() {
    const totals = Object.fromEntries(REASONS.map(reason => [reason, 0]));
    errors().forEach(item => { if (item.reason && Object.prototype.hasOwnProperty.call(totals, item.reason)) totals[item.reason]++; });
    return Object.entries(totals).sort((a, b) => b[1] - a[1]);
  }
  function priorityRows() {
    const diag = diagnosticRecord();
    if (diag && Array.isArray(diag.weakest) && diag.weakest.length) return diag.weakest.slice(0, 3);
    return ['قدرات كمي', 'قدرات لفظي', 'تحصيلي'].map(exam => {
      const x = trackStats(exam);
      return { name: exam, exam, percent: x.percent || 0 };
    }).sort((a, b) => a.percent - b.percent).slice(0, 3);
  }
  function renderReviewHub() {
    const page = document.getElementById('reviewPage');
    if (!page) return;
    syncMasterySchedule();
    const dueE = dueErrors();
    const dueM = dueMastery();
    const reasons = reasonBreakdown();
    const reasonMax = Math.max(1, ...reasons.map(x => x[1]));
    const priorities = priorityRows();
    page.innerHTML = `<div class="s39-page s39-review-page">
      <div class="s39-main-title"><div><small>مركز التثبيت الذكي</small><b>المراجعة</b></div><button onclick="showPage('tasksPage')">خطة اليوم</button></div>
      <div class="s39-review-hero"><div><span>المستحق الآن</span><b>${dueE.length + dueM.length}</b><small>${dueE.length} أخطاء • ${dueM.length} تعريفات وقوانين</small></div><button onclick="s39OpenErrors()">ابدأ المراجعة</button></div>
      <div class="s39-review-grid"><button onclick="s39OpenErrors()"><i>↻</i><b>${dueE.length}</b><span>أخطاء تحتاج تثبيت</span></button><button onclick="showPage('tasksPage')"><i>✓</i><b>${dueM.length}</b><span>مراجعات إتقان</span></button></div>
      <div class="s39-section-head"><b>أولوياتك التعليمية</b><button onclick="showPage('statsPage')">تفصيل الأداء</button></div>
      <div class="s39-priorities">${priorities.map((item, i) => `<div><strong>${i + 1}</strong><span><b>${esc(item.name)}</b><small>${esc(item.exam || '')} • إتقان ${Number(item.percent || 0)}%</small></span></div>`).join('')}</div>
      <div class="s39-section-head"><b>أسباب الأخطاء</b><span>يساعدك هذا على علاج السبب لا السؤال فقط</span></div>
      <div class="s39-reason-chart">${reasons.map(([name, count]) => `<div><span>${esc(name)}</span><i><em style="width:${Math.round((count / reasonMax) * 100)}%"></em></i><b>${count}</b></div>`).join('')}</div>
      <div class="s39-review-tip"><b>قاعدة سهيل</b><span>المعلومة التي أخطأت فيها اليوم تعود لك بعد يوم، ثم 3، 7، 14 و30 يومًا حتى تثبت.</span></div>
      ${nav('review')}
    </div>`;
    setPageMode('reviewPage');
  }

  function renderPerformanceJourney() {
    const page = document.getElementById('statsPage');
    if (!page) return;
    const p = prediction();
    const rows = history().slice(0, 8);
    const tracks = ['قدرات كمي', 'قدرات لفظي', 'تحصيلي'].map(exam => ({ exam, ...trackStats(exam) }));
    const overall = rows.length ? Math.round(avg(rows.map(x => x.percent || 0))) : (diagnosticRecord()?.percent || 0);
    const speed = rows.length ? Math.round(avg(rows.map(x => x.avgSec || 0).filter(Boolean))) : 0;
    const consistency = rows.length > 1 ? Math.max(0, 100 - Math.round(Math.sqrt(avg(rows.map(x => Math.pow(Number(x.percent || 0) - overall, 2)))) * 4)) : 0;
    const trend = rows.slice().reverse();
    const trendMax = Math.max(1, ...trend.map(x => Number(x.percent || 0)));
    page.innerHTML = `<div class="s39-page s39-performance-page">${header('أين وصلت؟', 'قراءة واضحة لمستواك واتجاهك', "showPage('homePage')")}
      <div class="s39-performance-hero"><span>الدرجة المتوقعة حاليًا</span><b>${p.ready ? `${p.low}–${p.high}` : '—'}</b><small>${esc(p.confidence)} • تتغير مع كل محاولة جديدة</small></div>
      <div class="s39-metric-grid"><div><b>${overall || '—'}</b><span>متوسط الدقة</span></div><div><b>${speed || '—'}</b><span>ثانية/سؤال</span></div><div><b>${consistency || '—'}</b><span>ثبات الأداء</span></div></div>
      <div class="s39-section-head"><b>المسارات الرئيسية</b></div>
      <div class="s39-tracks">${tracks.map(t => `<div class="s39-track"><div class="s39-track-top"><b>${esc(t.exam)}</b><span>${t.percent || 0}%</span></div><div class="s39-progress"><i style="width:${t.percent || 0}%"></i></div><small>${t.attempts ? `${t.attempts} محاولات • آخر نتيجة ${t.last}%` : 'لم يبدأ القياس بعد'}</small></div>`).join('')}</div>
      <div class="s39-section-head"><b>اتجاه آخر المحاولات</b><span>${rows.length ? 'الأحدث جهة اليسار' : 'ابدأ اختبارًا لظهور الاتجاه'}</span></div>
      <div class="s39-trend">${trend.length ? trend.map(x => `<div title="${esc(x.exam)} ${x.percent}%"><i style="height:${Math.max(8, Math.round((Number(x.percent || 0) / trendMax) * 100))}%"></i><small>${Number(x.percent || 0)}</small></div>`).join('') : '<div class="s39-empty">لا توجد محاولات مسجلة بعد.</div>'}</div>
      <div class="s39-improve-card"><b>${p.ready ? `لرفع التوقع فوق ${Math.min(100, p.high + 3)}` : 'لبناء توقع موثوق'}</b><span>${!diagnosticRecord() ? 'ابدأ بالاختبار التشخيصي.' : dueErrors().length ? `راجع ${dueErrors().length} أخطاء مستحقة قبل اختبار جديد.` : 'نفّذ اختبارًا قصيرًا في أضعف مسار ثم راقب الثبات.'}</span><button onclick="${!diagnosticRecord() ? 's39OpenDiagnostic()' : dueErrors().length ? 's39OpenErrors()' : `s39StartFocusedPractice('${esc(weakestTrack().exam)}')`}">ابدأ الخطوة التالية</button></div>
      <div class="s39-prediction-note">هذا التوقع مؤشر تعليمي داخلي، وليس تحويلًا رسميًا مضمونًا لدرجة قياس.</div>
    </div>`;
    setPageMode('statsPage');
  }

  function renderTasksPage() {
    const page = ensurePage('tasksPage');
    const tasks = dailyTasks();
    const done = planState().today;
    const progress = planProgress();
    const mastery = dueMastery().slice(0, 6);
    page.innerHTML = `<div class="s39-page s39-tasks-page">${header('مهام اليوم', 'خطة قصيرة تتغير حسب أدائك', "showPage('homePage')")}
      <div class="s39-plan-hero"><div class="s39-plan-ring" style="--p:${pct(progress.done, progress.total)}"><b>${progress.done}/${progress.total}</b></div><div><b>${progress.done === progress.total ? 'أكملت رحلة اليوم 🎉' : 'خطوات واضحة، بدون تشتت'}</b><span>${progress.total - progress.done} مهام متبقية</span></div></div>
      <div class="s39-task-list">${tasks.map(task => `<div class="s39-task ${done[task.id] ? 'done' : ''}"><button class="s39-task-check" onclick="s39ToggleTask('${task.id}')">${done[task.id] ? '✓' : ''}</button><button class="s39-task-body" onclick="${task.action}"><i>${task.icon}</i><span><b>${esc(task.title)}</b><small>${esc(task.detail)}</small></span><em>‹</em></button></div>`).join('')}</div>
      <div class="s39-section-head"><b>مراجعات الإتقان المستحقة</b><button onclick="showPage('reviewPage')">مركز المراجعة</button></div>
      <div class="s39-mastery-due">${mastery.length ? mastery.map(item => { const l = masteryLabel(item.key); return `<div><span><b>${esc(l.title)}</b><small>${esc(l.type)} • ${esc(l.unit || l.stage)}</small></span><button onclick="s39ReviewMastery('${esc(item.key)}',true)">أتقنت</button><button class="again" onclick="s39ReviewMastery('${esc(item.key)}',false)">أعدها</button></div>`; }).join('') : '<div class="s39-empty">لا توجد مراجعات مستحقة الآن.</div>'}</div>
      ${nav('tasks')}
    </div>`;
    setPageMode('tasksPage');
  }
  window.s39ToggleTask = function (id) { const done = !!planState().today[id]; setTaskDone(id, !done); };
  window.s39ReviewMastery = function (itemKey, mastered) {
    const schedule = masterySchedule();
    const item = schedule[itemKey] || { key: itemKey, repetition: 0 };
    if (mastered) {
      item.repetition = Number(item.repetition || 0) + 1;
      item.status = 'mastered';
      item.dueAt = Date.now() + INTERVALS[Math.min(item.repetition - 1, INTERVALS.length - 1)] * DAY;
    } else {
      item.repetition = 0;
      item.status = 'review';
      item.dueAt = Date.now() + DAY;
    }
    item.updatedAt = Date.now();
    schedule[itemKey] = item;
    saveMasterySchedule(schedule);
    if (!dueMastery().length) setTaskDone('mastery', true);
    renderTasksPage();
  };
  window.s39OpenQuestionBank = function () {
    const weak = weakestTrack();
    openExamSetup(weak && weak.exam ? weak.exam : 'قدرات كمي');
  };

  window.s39StartFocusedPractice = function (exam) {
    openExamSetup(exam);
    setTimeout(() => {
      const weak = weakestTrack();
      const sections = typeof getExamMainSections === 'function' ? getExamMainSections(exam) : [];
      if (weak.exam === exam && sections.length) selectedMainSections = [sections[sections.length - 1].name];
      if (typeof renderSectionChecklist === 'function') renderSectionChecklist();
    }, 80);
  };

  function recordExamErrors() {
    if (!Array.isArray(activeQuestions) || !Array.isArray(questionResults)) return;
    const map = Object.fromEntries(errors().map(x => [x.id, x]));
    activeQuestions.forEach((q, i) => {
      const r = questionResults[i];
      if (!r || !r.answered) return;
      const id = String(q.id || q.question || `q-${i}`);
      if (r.correct) {
        if (map[id]) {
          map[id].mastered = true;
          map[id].repetition = Number(map[id].repetition || 0) + 1;
          map[id].dueAt = Date.now() + INTERVALS[Math.min(map[id].repetition, INTERVALS.length - 1)] * DAY;
          map[id].lastCorrectAt = Date.now();
        }
        return;
      }
      const choices = Array.isArray(q.choices) ? q.choices : (q.options || []);
      const previous = map[id] || {};
      map[id] = {
        ...previous,
        id,
        exam: q.exam || currentExam,
        category: q.category || '', skill: q.skill || q.category || '', subject: q.subject || '', unit: q.unit || '',
        question: q.question || '', choices,
        selectedIndex: Number.isInteger(r.selectedIndex) ? r.selectedIndex : null,
        selectedText: Number.isInteger(r.selectedIndex) ? (choices[r.selectedIndex] || '') : 'لم تتم الإجابة',
        correctIndex: Number(q.correct), correctText: choices[Number(q.correct)] || q.answer || '',
        explain: q.explain || q.explanation || '', reason: previous.reason || '', note: previous.note || '',
        mastered: false, repetition: 0, dueAt: Date.now(), lastWrongAt: Date.now(), attempts: Number(previous.attempts || 0) + 1
      };
    });
    saveErrors(Object.values(map).sort((a, b) => Number(b.lastWrongAt || 0) - Number(a.lastWrongAt || 0)));
  }
  window.s39OpenErrors = function () { activatePage('errorReviewPage'); setPageMode('errorReviewPage'); renderErrorsPage(); };
  function renderErrorsPage() {
    const page = ensurePage('errorReviewPage');
    const all = errors();
    const source = errorFilter === 'due' ? dueErrors() : all;
    page.innerHTML = `<div class="s39-page">${header('مراجعة الأخطاء', 'الخطأ يتحول إلى خطوة تعلم', "showPage('homePage')")}
      <div class="s39-filter"><button class="${errorFilter === 'due' ? 'active' : ''}" onclick="s39ErrorFilter('due')">المستحقة ${dueErrors().length}</button><button class="${errorFilter === 'all' ? 'active' : ''}" onclick="s39ErrorFilter('all')">كل الأخطاء ${all.length}</button></div>
      <div class="s39-error-list">${source.length ? source.map(item => `<div class="s39-error-card ${item.mastered ? 'mastered' : ''}">
        <div class="s39-error-meta"><span>${esc(item.exam)}</span><span>${esc(item.skill)}</span><span>تكررت ${item.attempts || 1}</span></div>
        <div class="s39-error-q">${esc(item.question)}</div>
        <div class="s39-answer wrong"><b>إجابتك:</b> ${esc(item.selectedText)}</div><div class="s39-answer correct"><b>الصحيح:</b> ${esc(item.correctText)}</div>
        ${item.explain ? `<div class="s39-explain">${esc(item.explain)}</div>` : ''}
        <div class="s39-reason-title">وش كان سبب الخطأ؟</div><div class="s39-reasons">${REASONS.map(reason => `<button class="${item.reason === reason ? 'active' : ''}" onclick="s39SetErrorReason('${esc(item.id)}','${esc(reason)}')">${esc(reason)}</button>`).join('')}</div>
        <div class="s39-error-actions"><button onclick="s39MasterError('${esc(item.id)}')">فهمت الآن</button>${item.subject || item.unit ? `<button class="secondary" onclick="s39OpenErrorSummary('${esc(item.subject)}','${esc(item.unit)}','${esc(item.exam)}')">راجع الملخص</button>` : ''}</div>
      </div>`).join('') : '<div class="s39-empty">لا توجد أخطاء مستحقة. استمر في التدريب الذكي.</div>'}</div>
    </div>`;
  }
  window.s39ErrorFilter = function (value) { errorFilter = value; renderErrorsPage(); };
  window.s39SetErrorReason = function (id, reason) {
    const list = errors(); const item = list.find(x => x.id === id); if (item) item.reason = reason; saveErrors(list); renderErrorsPage();
  };
  window.s39MasterError = function (id) {
    const list = errors(); const item = list.find(x => x.id === id); if (!item) return;
    item.mastered = true; item.repetition = Number(item.repetition || 0) + 1;
    item.dueAt = Date.now() + INTERVALS[Math.min(item.repetition - 1, INTERVALS.length - 1)] * DAY;
    item.reviewedAt = Date.now(); saveErrors(list);
    if (!dueErrors().length) setTaskDone('errors', true); renderErrorsPage();
  };
  window.s39OpenErrorSummary = function (subject, unit, exam) {
    if (typeof openSummaryUnit === 'function' && subject && unit) return openSummaryUnit(subject, unit, exam);
    s28SummariesGateway();
  };

  function matchingSummaryItems(name) {
    const term = String(name || '').trim();
    return (Array.isArray(smartSummaries) ? smartSummaries : []).filter(x => [x.subject, x.unit, x.title, x.category, x.skill].some(v => String(v || '').includes(term))).slice(0, 8);
  }
  window.s39OpenSkillHub = function (name) {
    const tahsili = ['فيزياء', 'كيمياء', 'رياضيات', 'أحياء', 'الأحياء وعلم البيئة'].includes(name);
    const quant = ['حسابية', 'جبرية', 'هندسية', 'تحليل بيانات وإحصاء'].includes(name);
    const exam = tahsili ? 'تحصيلي' : quant ? 'قدرات كمي' : 'قدرات لفظي';
    skillHubState = { name, exam };
    activatePage('skillHubPage'); setPageMode('skillHubPage'); renderSkillHub();
  };
  function renderSkillHub() {
    const page = ensurePage('skillHubPage');
    const state = skillHubState || { name: 'مهارة', exam: 'قدرات كمي' };
    const qRows = questions.filter(q => q.exam === state.exam && [q.category, q.skill, q.subject, q.unit].some(v => String(v || '').includes(state.name.replace('ية', ''))));
    const summariesRows = matchingSummaryItems(state.name);
    const skills = Array.from(new Set(qRows.map(q => q.skill || q.category).filter(Boolean))).slice(0, 6);
    page.innerHTML = `<div class="s39-page">${header(state.name, state.exam, "s28SummariesGateway()")}
      <div class="s39-skill-overview"><div><b>${qRows.length}</b><span>سؤال مرتبط</span></div><div><b>${skills.length}</b><span>مهارات فرعية</span></div><div><b>${summariesRows.length}</b><span>بطاقات جاهزة</span></div></div>
      <div class="s39-section-head"><b>خريطة القسم</b></div><div class="s39-skill-map">${skills.length ? skills.map((skill, i) => `<div><strong>${i + 1}</strong><span><b>${esc(skill)}</b><small>افهم الفكرة ← طبّق ← راجع الخطأ</small></span></div>`).join('') : '<div class="s39-empty">سيظهر المحتوى هنا بعد تصنيفه من لوحة الإدارة.</div>'}</div>
      ${summariesRows.length ? `<div class="s39-section-head"><b>بطاقات مرتبطة</b></div><div class="s39-summary-snippets">${summariesRows.map(x => `<div><b>${esc(x.title || x.unit || state.name)}</b><p>${esc(String(x.simple_idea || x.summary || '').slice(0, 180))}</p></div>`).join('')}</div>` : ''}
      <button class="s39-next" onclick="s39PracticeSkill('${esc(state.exam)}','${esc(state.name)}')">تدرّب على هذا القسم</button>
    </div>`;
  }
  window.s39PracticeSkill = function (exam, name) {
    openExamSetup(exam);
    setTimeout(() => {
      const sections = typeof getExamMainSections === 'function' ? getExamMainSections(exam) : [];
      const match = sections.find(s => s.name.includes(name.replace('ية', '')) || name.includes(s.name.replace('مسائل ', '')));
      if (match) selectedMainSections = [match.name];
      if (typeof renderSectionChecklist === 'function') renderSectionChecklist();
    }, 80);
  };

  window.s39EnableReminder = async function () {
    write('reminders', { enabled: true, hour: 19, updatedAt: Date.now() });
    if ('Notification' in window) {
      try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') new Notification('سهيل', { body: 'تم تفعيل تذكير سهيل. جلسة قصيرة كل يوم تكفي.' });
      } catch (_) {}
    }
    toast('تم حفظ تذكير سهيل للمساء. إشعارات التطبيق الأصلية جاهزة ضمن ملف نسخة الجوال.');
  };
  function toast(message) {
    let el = document.getElementById('s39Toast');
    if (!el) { el = document.createElement('div'); el.id = 's39Toast'; document.body.appendChild(el); }
    el.textContent = message; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 3500);
  }
  function maybeDailyToast() {
    const last = localStorage.getItem(key('toast_day'));
    if (last === today()) return;
    localStorage.setItem(key('toast_day'), today());
    setTimeout(() => toast(companionMessage()), 3600);
  }

  function installStyles() {
    if (document.getElementById('s39Styles')) return;
    const style = document.createElement('style'); style.id = 's39Styles';
    style.textContent = `
      :root{--s39-navy:#10255c;--s39-blue:#159bd0;--s39-green:#29bd82;--s39-soft:#f4f9fc;--s39-line:#deebf2}
      #homePage{overflow:auto!important;height:100%!important;background:#f7fafc!important}.s39-home,.s39-page{font-family:'Tajawal',system-ui,sans-serif!important;direction:rtl;color:var(--s39-navy);min-height:100%;padding:18px 18px 112px;background:linear-gradient(180deg,#f7fbfd,#fff 42%,#f7fbfd)}
      .s39-home-top{display:flex;justify-content:space-between;align-items:center}.s39-hello{font-size:20px;font-weight:950}.s39-date{font-size:11px;font-weight:800;color:#75869a;margin-top:4px}.s39-bell{width:42px;height:42px;border:1px solid #e2edf3;border-radius:16px;background:#fff;color:var(--s39-blue);font-size:23px;box-shadow:0 9px 22px rgba(15,35,66,.07)}
      .s39-companion{margin-top:13px;border-radius:24px;padding:15px;background:linear-gradient(135deg,#eaf8ff,#ecfff5);display:grid;grid-template-columns:48px 1fr;gap:12px;align-items:center;border:1px solid #d8edf1}.s39-companion-mark{width:48px;height:48px;border-radius:18px;background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;display:grid;place-items:center;font-size:26px;font-weight:950}.s39-companion-title{font-size:16px;font-weight:950}.s39-companion-text{font-size:12px;line-height:1.6;color:#536a80;font-weight:800;margin-top:3px}
      .s39-diagnostic-call{margin-top:12px;border-radius:22px;padding:14px;background:#fff;border:1px solid #dceaf3;box-shadow:0 10px 22px rgba(15,35,66,.06);display:flex;justify-content:space-between;align-items:center;gap:10px}.s39-diagnostic-call b,.s39-diagnostic-call span{display:block}.s39-diagnostic-call b{font-size:15px}.s39-diagnostic-call span{font-size:11px;color:#718297;margin-top:4px}.s39-diagnostic-call button{border:0;border-radius:14px;background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;font-weight:900;padding:10px 12px;white-space:nowrap}
      .s39-score-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:13px}.s39-score-card{min-height:91px;border-radius:20px;background:#fff;border:1px solid #e2edf3;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(15,35,66,.05)}.s39-score-card span{font-size:10px;font-weight:850;color:#75869a}.s39-score-card b{font-size:21px;margin:4px 0}.s39-score-card small{font-size:9px;color:#7a8b9f}.s39-score-card.prediction{background:linear-gradient(145deg,#edf8ff,#f2fff7)}
      .s39-daily-cta{width:100%;margin-top:13px;border:0;border-radius:23px;background:linear-gradient(135deg,#159bd0,#29bd82);color:#fff;padding:15px 17px;display:flex;align-items:center;justify-content:space-between;text-align:right;box-shadow:0 15px 28px rgba(20,155,180,.2)}.s39-daily-cta b,.s39-daily-cta small{display:block}.s39-daily-cta b{font-size:17px}.s39-daily-cta small{font-size:10px;opacity:.86;margin-top:4px}.s39-daily-cta i{font-size:27px;font-style:normal}
      .s39-section-head{display:flex;align-items:center;justify-content:space-between;margin:17px 2px 9px}.s39-section-head b{font-size:16px}.s39-section-head button{border:0;background:transparent;color:#178fc2;font-size:11px;font-weight:900}.s39-tracks{display:grid;gap:8px}.s39-track{border-radius:19px;padding:12px;background:#fff;border:1px solid #e1edf3}.s39-track-top{display:flex;justify-content:space-between;font-size:13px}.s39-track-top span{font-weight:950;color:#168fb8}.s39-progress{height:7px;border-radius:999px;background:#edf3f6;margin:8px 0 5px;overflow:hidden}.s39-progress i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--s39-blue),var(--s39-green))}.s39-track small{font-size:9.5px;color:#7a8b9f}
      .s39-insight-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.s39-insight-grid button{min-height:70px;border:1px solid #e0ebf2;border-radius:19px;background:#fff;text-align:right;padding:12px;display:flex;flex-direction:column}.s39-insight-grid b{font-size:20px;color:#148fb8}.s39-insight-grid span{font-size:10px;font-weight:850;color:#65788c}.s39-prediction-note{font-size:9.5px;color:#7b8998;text-align:center;line-height:1.6;margin:11px 10px 0}
      .s39-main-nav{position:absolute;left:14px;right:14px;bottom:9px;height:70px;border-radius:25px;background:rgba(255,255,255,.97);box-shadow:0 13px 35px rgba(15,35,66,.13);border:1px solid #e7eff4;display:grid;grid-template-columns:repeat(5,1fr);align-items:center;z-index:50}.s39-nav-item{border:0;background:transparent;color:#7a899a;display:flex;flex-direction:column;align-items:center;gap:4px;font-family:'Tajawal',sans-serif}.s39-nav-item span{font-size:20px}.s39-nav-item small{font-size:9.5px;font-weight:900}.s39-nav-item.active{color:#178fc2}.s39-nav-item.active span{width:38px;height:38px;border-radius:15px;background:linear-gradient(135deg,#e7f7ff,#e9fff3);display:grid;place-items:center}
      .s39-header{position:relative;margin:-18px -18px 16px;min-height:154px;overflow:hidden;border-radius:0 0 28px 28px;background:radial-gradient(circle at 15% 8%,rgba(0,169,224,.18),transparent 31%),radial-gradient(circle at 96% 100%,rgba(36,200,126,.22),transparent 38%),linear-gradient(135deg,#fff,#f7fbff 58%,#eaf8fa);border-bottom:1px solid #d8e8ee}.s39-header:after{content:'';position:absolute;left:-70px;bottom:-82px;width:230px;height:190px;border-radius:50%;background:linear-gradient(135deg,rgba(0,169,224,.15),rgba(35,207,142,.11))}.s39-back{position:absolute;right:14px;top:14px;z-index:4;width:42px;height:42px;border:0;border-radius:50%;background:#fff;box-shadow:0 10px 23px rgba(15,35,66,.13);display:grid;place-items:center}.s39-back svg{width:22px;height:22px;fill:none;stroke:#15365d;stroke-width:4.2;stroke-linecap:round;stroke-linejoin:round}.s39-formula{position:absolute;color:#8ccce3;font-weight:900;opacity:.5}.s39-formula.f1{top:30px;left:90px}.s39-formula.f2{top:73px;left:38px}.s39-header-copy{position:absolute;left:20px;right:20px;bottom:23px;text-align:center;z-index:2}.s39-header-title{font-size:30px;font-weight:950}.s39-header-sub{font-size:11px;font-weight:850;color:#526b81;margin-top:5px}
      .s39-diag-progress{height:7px;background:#e9f0f4;border-radius:999px;overflow:hidden;margin:3px 0 14px}.s39-diag-progress i{display:block;height:100%;background:linear-gradient(90deg,var(--s39-blue),var(--s39-green))}.s39-diag-meta{display:flex;gap:7px}.s39-diag-meta span,.s39-error-meta span{border-radius:999px;background:#edf7fb;color:#177fa5;padding:5px 8px;font-size:9.5px;font-weight:900}.s39-question{font-size:20px;font-weight:950;line-height:1.75;margin:18px 2px}.s39-options{display:grid;gap:9px}.s39-options button{min-height:58px;border:1px solid #dce9f1;border-radius:19px;background:#fff;text-align:right;padding:10px 12px;font-family:'Tajawal';font-size:14px;font-weight:850;color:#17365d;display:flex;align-items:center;gap:10px}.s39-options button span{width:34px;height:34px;border-radius:13px;background:#eef6fa;display:grid;place-items:center}.s39-options button.selected{border-color:#20ae91;background:#effdf7}.s39-options button.selected span{background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff}.s39-next{width:100%;min-height:50px;border:0;border-radius:18px;background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;font-family:'Tajawal';font-size:15px;font-weight:950;margin-top:15px}.s39-next:disabled{opacity:.4}
      .s39-result-hero{border-radius:26px;padding:22px;background:linear-gradient(135deg,#159bd0,#29bd82);color:#fff;text-align:center}.s39-result-hero small,.s39-result-hero span{display:block}.s39-result-hero b{font-size:46px;display:block;margin:4px}.s39-result-tracks{display:grid;gap:9px;margin-top:13px}.s39-result-tracks>div{border:1px solid #e0ebf1;border-radius:19px;background:#fff;padding:12px;display:grid;grid-template-columns:1fr auto;gap:6px}.s39-result-tracks i{grid-column:1/-1;height:6px;background:#edf2f5;border-radius:99px;overflow:hidden}.s39-result-tracks em{display:block;height:100%;background:linear-gradient(90deg,var(--s39-blue),var(--s39-green))}.s39-result-pred{margin-top:12px;border-radius:21px;background:#effaf6;padding:15px;text-align:center}.s39-result-pred span,.s39-result-pred small{display:block}.s39-result-pred b{font-size:28px;color:#148f84}.s39-priorities{display:grid;gap:8px}.s39-priorities>div,.s39-skill-map>div{border:1px solid #e1ebf1;border-radius:18px;background:#fff;padding:11px;display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:center}.s39-priorities strong,.s39-skill-map strong{width:34px;height:34px;border-radius:12px;background:#eaf8f5;color:#168f7b;display:grid;place-items:center}.s39-priorities b,.s39-priorities small,.s39-skill-map b,.s39-skill-map small{display:block}.s39-priorities small,.s39-skill-map small{font-size:9.5px;color:#75869a;margin-top:3px}
      .s39-plan-hero{border-radius:24px;background:linear-gradient(135deg,#eaf8ff,#effff7);padding:15px;display:flex;align-items:center;gap:14px;border:1px solid #d8ebef}.s39-plan-ring{--p:0;width:64px;height:64px;border-radius:50%;background:conic-gradient(var(--s39-green) calc(var(--p)*1%),#dceaf0 0);display:grid;place-items:center}.s39-plan-ring:before{content:'';grid-area:1/1;width:49px;height:49px;border-radius:50%;background:#fff}.s39-plan-ring b{grid-area:1/1;z-index:1}.s39-plan-hero>div:last-child b,.s39-plan-hero>div:last-child span{display:block}.s39-plan-hero>div:last-child span{font-size:11px;color:#667b8f;margin-top:5px}.s39-task-list{display:grid;gap:9px;margin-top:13px}.s39-task{border:1px solid #e0ebf1;border-radius:20px;background:#fff;display:grid;grid-template-columns:48px 1fr;overflow:hidden}.s39-task.done{opacity:.65}.s39-task-check{border:0;border-left:1px solid #e6eef2;background:#f7fbfc;color:#fff;font-size:18px}.s39-task.done .s39-task-check{background:#28bd82}.s39-task-body{border:0;background:transparent;display:grid;grid-template-columns:38px 1fr 20px;align-items:center;gap:9px;text-align:right;padding:11px;font-family:'Tajawal';color:#17365d}.s39-task-body>i{font-size:20px;font-style:normal}.s39-task-body b,.s39-task-body small{display:block}.s39-task-body b{font-size:14px}.s39-task-body small{font-size:9.5px;color:#74869a;margin-top:4px}.s39-task-body em{font-style:normal;font-size:23px;color:#23a985}.s39-mastery-due{display:grid;gap:8px}.s39-mastery-due>div{border:1px solid #e1ecf2;border-radius:18px;background:#fff;padding:10px;display:grid;grid-template-columns:1fr auto auto;gap:7px;align-items:center}.s39-mastery-due b,.s39-mastery-due small{display:block}.s39-mastery-due small{font-size:9px;color:#7b8998}.s39-mastery-due button{border:0;border-radius:12px;background:#e9faf4;color:#16896e;padding:8px;font-weight:900}.s39-mastery-due button.again{background:#fff5e9;color:#b16917}
      .s39-filter{display:grid;grid-template-columns:1fr 1fr;gap:8px}.s39-filter button{height:42px;border:1px solid #dfeaf0;border-radius:15px;background:#fff;font-weight:900;color:#6d7f92}.s39-filter button.active{background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;border:0}.s39-error-list{display:grid;gap:12px;margin-top:12px}.s39-error-card{border:1px solid #e1eaf0;border-radius:22px;background:#fff;padding:14px;box-shadow:0 9px 22px rgba(15,35,66,.05)}.s39-error-card.mastered{border-color:#c8ebdc}.s39-error-meta{display:flex;gap:6px;flex-wrap:wrap}.s39-error-q{font-size:15px;font-weight:950;line-height:1.7;margin:12px 0}.s39-answer{border-radius:13px;padding:8px 10px;font-size:11px;margin-top:6px}.s39-answer.wrong{background:#fff0f0;color:#9b3535}.s39-answer.correct{background:#ecfbf4;color:#167657}.s39-explain{font-size:11px;line-height:1.7;color:#596e82;background:#f7fafc;border-radius:14px;padding:9px;margin-top:8px}.s39-reason-title{font-size:11px;font-weight:950;margin-top:11px}.s39-reasons{display:flex;gap:6px;overflow-x:auto;margin-top:6px}.s39-reasons button{white-space:nowrap;border:1px solid #dfe8ee;border-radius:999px;background:#fff;padding:6px 9px;font-size:9px;font-weight:900}.s39-reasons button.active{background:#eaf9f4;color:#16866d;border-color:#c5eadb}.s39-error-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:11px}.s39-error-actions button{height:40px;border:0;border-radius:14px;background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;font-weight:900}.s39-error-actions button.secondary{background:#edf6fa;color:#167fa5}
      .s39-skill-overview{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.s39-skill-overview>div{border:1px solid #e0ebf1;border-radius:19px;background:#fff;padding:13px;text-align:center}.s39-skill-overview b,.s39-skill-overview span{display:block}.s39-skill-overview b{font-size:22px;color:#168fb0}.s39-skill-overview span{font-size:9px;color:#718399}.s39-skill-map,.s39-summary-snippets{display:grid;gap:8px}.s39-summary-snippets>div{border:1px solid #e0ebf1;border-radius:18px;background:#fff;padding:12px}.s39-summary-snippets p{font-size:11px;line-height:1.7;color:#65798c;margin:5px 0 0}.s39-empty{border:1px dashed #cfdde5;border-radius:20px;background:#fafcfd;padding:20px;text-align:center;color:#7a8998;font-size:12px;font-weight:850}
      .s39-main-title{display:flex;justify-content:space-between;align-items:center;padding:12px 2px 16px}.s39-main-title small,.s39-main-title b{display:block}.s39-main-title small{font-size:10px;color:#72859a}.s39-main-title b{font-size:28px;color:#15365d}.s39-main-title button{border:0;border-radius:15px;background:#eaf8f5;color:#15866e;padding:10px 12px;font-weight:900}.s39-review-hero{border-radius:25px;background:linear-gradient(135deg,#159fd1,#27bd83);color:#fff;padding:18px;display:flex;align-items:center;justify-content:space-between;gap:12px}.s39-review-hero span,.s39-review-hero b,.s39-review-hero small{display:block}.s39-review-hero b{font-size:36px}.s39-review-hero small{font-size:10px;opacity:.9}.s39-review-hero button{border:0;border-radius:15px;background:#fff;color:#168e83;padding:11px 13px;font-weight:950}.s39-review-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:10px}.s39-review-grid button{border:1px solid #dfeaf0;border-radius:20px;background:#fff;padding:14px;text-align:right;color:#18375d}.s39-review-grid i,.s39-review-grid b,.s39-review-grid span{display:block}.s39-review-grid i{font-style:normal;font-size:20px}.s39-review-grid b{font-size:25px;margin-top:4px}.s39-review-grid span{font-size:10px;color:#718397}.s39-reason-chart{display:grid;gap:8px}.s39-reason-chart>div{display:grid;grid-template-columns:82px 1fr 22px;gap:8px;align-items:center;font-size:10px}.s39-reason-chart>div>i{height:8px;border-radius:99px;background:#e8f0f4;overflow:hidden}.s39-reason-chart em{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--s39-blue),var(--s39-green))}.s39-review-tip,.s39-improve-card{margin-top:14px;border-radius:20px;background:#f1faf7;border:1px solid #d7ece5;padding:14px}.s39-review-tip b,.s39-review-tip span,.s39-improve-card b,.s39-improve-card span{display:block}.s39-review-tip span,.s39-improve-card span{font-size:10.5px;color:#617789;line-height:1.7;margin-top:4px}.s39-performance-hero{border-radius:25px;background:linear-gradient(135deg,#153d73,#169fc4 58%,#29bd83);color:#fff;text-align:center;padding:20px}.s39-performance-hero span,.s39-performance-hero b,.s39-performance-hero small{display:block}.s39-performance-hero b{font-size:43px;margin:4px}.s39-performance-hero small{font-size:10px;opacity:.88}.s39-metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.s39-metric-grid>div{border:1px solid #dfeaf0;border-radius:18px;background:#fff;padding:12px;text-align:center}.s39-metric-grid b,.s39-metric-grid span{display:block}.s39-metric-grid b{font-size:20px;color:#188fa3}.s39-metric-grid span{font-size:9px;color:#74879a;margin-top:3px}.s39-trend{min-height:120px;border:1px solid #e0eaf0;border-radius:21px;background:#fff;padding:14px;display:flex;align-items:flex-end;gap:8px}.s39-trend>div:not(.s39-empty){height:94px;flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:3px}.s39-trend i{display:block;width:100%;max-width:25px;border-radius:8px 8px 3px 3px;background:linear-gradient(180deg,var(--s39-blue),var(--s39-green))}.s39-trend small{font-size:8px;color:#6f8194}.s39-improve-card button{margin-top:10px;border:0;border-radius:14px;background:linear-gradient(135deg,var(--s39-blue),var(--s39-green));color:#fff;padding:10px 12px;font-weight:950;font-family:'Tajawal'}
      #s39Toast{position:fixed;left:22px;right:22px;bottom:92px;z-index:9999;transform:translateY(30px);opacity:0;pointer-events:none;background:#12335b;color:#fff;border-radius:18px;padding:13px;text-align:center;font-family:'Tajawal';font-size:11px;font-weight:850;transition:.25s}#s39Toast.show{transform:translateY(0);opacity:1}
      body.s39-force-main #s28LiftNav,body.s39-force-exam #s28LiftNav,body.s39-force-exam .suhail-tabbar,body.s39-force-exam .s39-main-nav,body.s39-force-exam .bottom-nav{display:none!important}body.s39-force-branch #s28LiftNav{display:block!important}body.s39-force-main #s28LiftNav{display:none!important}
      .s28-logo-word,.s28-logo-word:after{display:none!important}.s28-back-btn{right:14px!important;left:auto!important}.s28-hero-sub:empty{display:none!important}
      @media(max-width:430px){.s39-home,.s39-page{padding-left:14px;padding-right:14px}.s39-header{margin-left:-14px;margin-right:-14px}.s39-score-card b{font-size:19px}.s39-question{font-size:18px}.s39-main-nav{left:10px;right:10px}}
    `;
    document.head.appendChild(style);
  }

  function patchSummaries() {
    window.s28ComingSoon = function (name) { s39OpenSkillHub(name); };
    const lift = document.getElementById('s28LiftNav');
    if (lift) {
      const buttons = lift.querySelectorAll('.s28-lift-panel button');
      if (buttons[3]) buttons[3].setAttribute('onclick', "showPage('tasksPage');document.body.classList.remove('s28-nav-open')");
      if (buttons[4]) { buttons[4].textContent = 'الحساب'; buttons[4].setAttribute('onclick', "showPage('profilePage');document.body.classList.remove('s28-nav-open')"); }
    }
  }
  function patchSummaryCompletion() {
    if (window.__s39SummaryPatched || typeof window.openSummaryUnit !== 'function') return;
    window.__s39SummaryPatched = true;
    const oldOpenSummaryUnit = window.openSummaryUnit;
    window.openSummaryUnit = function () {
      setTaskDone('summary', true);
      return oldOpenSummaryUnit.apply(this, arguments);
    };
  }
  function patchFinishExam() {
    if (window.__s39FinishPatched || typeof window.finishExam !== 'function') return;
    window.__s39FinishPatched = true;
    const oldFinish = window.finishExam;
    window.finishExam = function () {
      const wasFinished = !!examFinished;
      const result = oldFinish.apply(this, arguments);
      if (!wasFinished) {
        try { recordExamErrors(); setTaskDone('practice', true); } catch (err) { console.error('S39 post exam', err); }
      }
      return result;
    };
  }
  function patchNavigation() {
    if (window.__s39ShowPatched) return;
    window.__s39ShowPatched = true;
    const oldShow = window.showPage;
    window.showPage = function (id) {
      if (id === 'tasksPage') { activatePage(id); renderTasksPage(); return; }
      if (id === 'reviewPage') { activatePage(id); renderReviewHub(); return; }
      if (id === 'statsPage') { activatePage(id); renderPerformanceJourney(); return; }
      if (id === 'diagnosticPage') { activatePage(id); renderDiagnostic(); return; }
      if (id === 'errorReviewPage') { activatePage(id); renderErrorsPage(); return; }
      if (id === 'skillHubPage') { activatePage(id); renderSkillHub(); return; }
      const result = typeof oldShow === 'function' ? oldShow.apply(this, arguments) : activatePage(id);
      setTimeout(() => {
        setPageMode(id);
        if (id === 'homePage') renderJourneyHome();
        if (id === 'tasksPage') renderTasksPage();
        if (id === 'reviewPage') renderReviewHub();
        if (id === 'statsPage') renderPerformanceJourney();
      }, 90);
      return result;
    };
  }
  function install() {
    if (window.SUHAIL_FOCUS_MODE) return;
    installStyles();
    ['diagnosticPage', 'tasksPage', 'errorReviewPage', 'skillHubPage'].forEach(ensurePage);
    updateVisit(); syncMasterySchedule();
    patchNavigation(); patchFinishExam(); patchSummaryCompletion(); patchSummaries();
    setTimeout(() => {
      const active = document.querySelector('.page.active');
      if (active && active.id === 'homePage') renderJourneyHome();
      if (active && active.id === 'reviewPage') renderReviewHub();
      if (active && active.id === 'statsPage') renderPerformanceJourney();
      setPageMode(active ? active.id : 'homePage');
      patchSummaries(); maybeDailyToast();
    }, 650);
    setInterval(() => {
      const active = document.querySelector('.page.active');
      if (active) setPageMode(active.id);
      patchFinishExam(); patchSummaryCompletion(); patchSummaries();
    }, 800);
    window.SUHAIL_JOURNEY_VERSION = VERSION;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install);
  else install();
})();
