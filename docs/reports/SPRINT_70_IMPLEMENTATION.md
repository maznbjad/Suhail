# Suhail Sprint 70 — Stability and unified experience

## Runtime

- Added an early storage guard before the legacy application script. When browser privacy settings block `localStorage`, Suhail falls back to in-memory storage instead of stopping on a blank screen.
- Added a splash fail-safe that removes the opening screen after 4.3 seconds even if another script fails.
- Added `scripts/preflight.py` to check dependencies, Python syntax, required files, JSON validity and data-folder write access before launch.
- Rebuilt `run_suhail.bat` with Python/Anaconda discovery, automatic dependency installation, dynamic ports from 8501 to 8510, LAN access and clearer failure messages.
- Increased the embedded application height to 960 pixels for safer mobile rendering.

## Unified interface

- Added a final design system with shared surfaces, borders, typography, controls, cards and navigation states.
- Standardized back icons and final bottom-navigation icon sizes/strokes.
- Historical duplicate navigation systems are hidden; the final navigation is hidden in authentication, onboarding and active questions.
- Added safe bottom spacing so content does not sit behind the fixed navigation.

## Dark mode

- Introduced final light/dark tokens for background, surfaces, text, muted text, borders and controls.
- Covered old and new cards, settings, forms, choices, question states, account pages, summaries, review pages and admin surfaces.
- Inputs, placeholders, notes, selected states and navigation now retain readable contrast.

## Student clarity

- The first setup screen now explains the journey in four numbered steps.
- The bottom navigation is removed during initial setup to avoid competing actions.
- A fixed “حفظ وابدأ رحلتي” action remains visible while the student scrolls through characters.
- The first home screen clearly explains the sequence: determine level, receive today’s plan, then review mistakes.

## Validation

- `python scripts/preflight.py`
- `python scripts/validate_project.py`
- `node --check src/ui/sprint70_boot.js`
- `node --check src/ui/sprint70_unified_app.js`
- Streamlit HTTP startup test
- Flask `/health` test
- Browser-level tests for blocked storage, splash removal, authentication navigation, onboarding navigation and dark-mode rendering
