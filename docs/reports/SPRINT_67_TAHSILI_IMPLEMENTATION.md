# Sprint 67 - Tahsili Question Bank, Phase 1

## Scope

This sprint starts the Tahsili bank without adding or changing any summaries. The existing curated physics summaries remain the only published summaries.

## Question bank

- 1,200 new Tahsili questions.
- 300 Physics.
- 300 Chemistry.
- 300 Mathematics.
- 300 Biology and Ecology.
- Visible public IDs continue from 263001 to 264200.
- The complete application bank is now 4,200 questions including the existing 3,000 Qudurat questions.

## Explanations

- Every question stores a verified explanation internally.
- Easy direct questions use `explanation_mode: none`, so the student is not shown unnecessary detail.
- Illustrated easy questions use a brief explanation.
- Medium and difficult questions use a full explanation.
- Close-option notes appear only when a distractor represents a realistic misconception or a formula for a related quantity.

## Images

- 165 new Tahsili questions include original SVG diagrams.
- Diagrams have transparent backgrounds and are displayed on the app's white image surface in both light and dark modes.
- No source watermarks, logos, screenshots, or full source pages are used.
- Images support zoom and have alternative text.
- Arabic labels were avoided inside SVG where bidirectional rendering could reduce clarity; short scientific symbols and numbers are used instead.

## App integration

- The home Test button now includes Tahsili alongside Quantitative and Verbal Qudurat.
- Tahsili setup automatically lists the four subjects as selectable sections.
- Biology is consistently named `الأحياء وعلم البيئة` in the scoring API.
- SQLite was rebuilt to match the JSON bank.

## Validation

- 4,200 unique internal IDs.
- Continuous public IDs: 260001-264200.
- Four distinct choices per question.
- Correct answer/index consistency.
- 300 questions for each Tahsili subject.
- All image files exist and all generated SVG files parse successfully.
- Python and JavaScript syntax checks passed.

## Important boundary

This is Phase 1 of the Tahsili bank. It creates a substantial internal testing bank and the complete ingestion structure. A later content-review phase should compare performance data and manually review wording by subject experts before public App Store release.
