# Sprint 85 — Account completion and interaction fixes

- First-time student accounts are locked to `studentSetupPage` until `onboardingDone=true`.
- All bottom navigation implementations are hidden during the locked setup state.
- A screen-level confirmation action remains visible and calls the canonical `s54SaveSetup()` flow.
- Home and account read the same `s54_profile_<user>` record and `avatarId`.
- Global UI typography is compacted without overriding Sprint 80 question-size variables.
- Mouse-wheel scrolling uses a faster capture handler; touch, picker wheels, and nested scrollers remain supported.
