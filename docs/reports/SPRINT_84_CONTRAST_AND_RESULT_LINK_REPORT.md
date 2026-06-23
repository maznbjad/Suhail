# Sprint 84 — Contrast and Result-Link Fix

## Root causes

1. Several old card-title classes still used `color: var(--ink)`. The legacy `--ink` value remained dark in some dark-mode cards, so fixing only `.main-section-title` did not fix the same problem in source cards and result cards.
2. The final-result cleanup in Sprint 68 removed `.result-answer-line` and recreated the student's answer as `.s68-result-choice`; therefore an unanswered-state fix that targeted only the original line could not own the final rendered text.
3. Sprint 72 read `window.activeQuestions`, while the main application declares `activeQuestions` and `questionResults` with top-level `let`. They are available as global lexical bindings but are not automatically properties on `window`, so result-card summary decoration could fail even when the question had an exact link.

## Fixes

- Added one semantic color system for card titles and subtitles across exam setup, source selection, results, summaries, home tools and account rows.
- Added a dedicated skipped-question state:
  - badge: `لم يُجب`
  - answer text: `لم تتم الإجابة`
  - warning color is readable in light and dark themes.
- Added a compatibility bridge for `activeQuestions` and `questionResults`.
- Added a direct, exact `فتح الملخص` action to each linked result card.
- The action opens the linked physics lesson and knowledge block, not a generic subject or unit page.

## Interactive QA

The interactive browser QA used the published UI with a reduced three-question physics fixture while retaining the same runtime modules and exact summary data.

- Dark source-card title contrast: **15.63:1**
- Dark source-card subtitle contrast: **10.14:1**
- Unanswered text contrast: **12.35:1**
- Unanswered badge changed to `لم يُجب`: passed
- Direct summary buttons generated for all three linked fixture questions: passed
- Mouse click opened `summariesPage`: passed
- Destination contained `وصلت من سؤال مرتبط`: passed
- JavaScript page errors: **0**

## Full-project checks

- Question bank: **5,400**
- Tahsili questions: **2,400**
- Exact question-summary links currently published: **600 physics questions**
- Python compilation: passed
- JavaScript syntax: passed
- `scripts/preflight.py`: passed
- Streamlit HTTP check: **200**
