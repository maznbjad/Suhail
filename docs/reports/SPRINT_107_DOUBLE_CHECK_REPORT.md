# Sprint 107 — Double-check correction

The second verification found a real RTL positioning defect in Sprint 106: `inset-inline-end` maps to the physical left in an RTL document and conflicted with `right`.

## Corrected
- Removed all logical inset writes from the back-button guard.
- Enforced physical `right` and reset physical `left` only.
- Added title safe zones to prevent overlap.
- Covered the active summary, PDF, account, diagnostic, and legacy top bars.
- Kept the PDF reader button on the right and corrected its chevron direction for Arabic navigation.
- Uses MutationObserver only; no new polling interval.
