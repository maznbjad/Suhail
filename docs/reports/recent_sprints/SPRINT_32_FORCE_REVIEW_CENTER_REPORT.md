# Sprint 32 — Force review center rendering

- Fixed why the review design did not appear.
- The old `renderPlanPage()` was still being called by `activatePage()` and overwriting the new review center.
- Patched `activatePage()` to call `s31RenderReviewPage()` for `reviewPage`.
- Added a guard inside `renderPlanPage()` so it delegates to the new review center.
- Updated static review page labels to match the new review design.
