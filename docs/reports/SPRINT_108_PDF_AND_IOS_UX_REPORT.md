# Sprint 108 - PDF Books + iPhone UX

## Content
- Added Physics 2 PDF (13 pages).
- Added Physics 3, semester one PDF (22 pages).
- Generated optimized WebP page assets.
- Generated selectable OCR layers for both books.
- Refactored the reader from one hard-coded book to a multi-book registry.

## UX
- Reader opens directly from the book card.
- All persistent chrome is hidden in reading mode.
- Back target stays on the physical right and respects safe areas.
- Highlight palette is positioned relative to the phone reader, not the browser viewport.
- Page images use lazy loading and async decoding.
- Last page and highlights are stored separately per book.
- Real mobile mode no longer draws a fake status bar.

## Release limitation
This sprint makes the design and UX suitable for migration into the planned Expo iOS app. The current Python/Streamlit package cannot be uploaded directly to App Store Connect.
