# Suhail Sprint 109 — No OCR Lightweight Reader

## Done
- Removed OCR text layers from the PDF reader.
- Removed text selection and text highlighting UI.
- Deleted OCR JSON assets:
  - `assets/summary_pdfs/physics1_ocr.json`
  - `assets/summary_pdfs/physics2_ocr.json`
  - `assets/summary_pdfs/physics31_ocr.json`
- Kept the lightweight PDF reading mode:
  - Full page inside iPhone frame on desktop preview.
  - Real full screen on mobile.
  - Only the 50% transparent back button remains.
  - Last page is still saved per book.
- Updated content-management text to describe PDF-only upload.

## Reason
OCR was useful only for text selection/highlighting, but it increases DOM size, memory use, startup cost and scroll work. Since the summaries are already designed as fixed pages, removing OCR improves speed and stability.
