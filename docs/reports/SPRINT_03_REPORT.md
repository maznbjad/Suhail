# Sprint 03/07 - Splash Timing & Sound Fix

## Fixed
- Splash was disappearing too fast, sometimes under half a second.
- SVG internal animation duration was extended.
- JS now enforces a minimum visible duration.
- New soft startup chime generated in `sounds/splash_soft.wav`.
- Added WebAudio fallback.
- Added first-gesture retry for browsers that block autoplay.

## Current behavior
- Splash shows for about 3.3 seconds.
- Sprint testing mode is enabled: splash appears on each fresh load so timing can be verified.
- If autoplay is blocked, the app shows a subtle hint: "المس الشاشة للصوت".

## Next sprint candidate
- Home page identity polish after splash.
- Make splash show once after approval.
