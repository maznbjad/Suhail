# Passage Lock Fix

## الأساس
تم البناء على:
`suhail_v20_verbal_samples_sprint02_arabic_digits_passage_fix.zip`

## التعديل
- عند السحب فوق مربع نص استيعاب المقروء:
  - يتحرك نص القطعة فقط.
  - الشاشة/الصفحة نفسها تثبت ولا تنزل.
- في الكمبيوتر:
  - سكرول الماوس فوق مربع القطعة يحرك نص القطعة فقط.
- أخفيت أي مؤشر/سلايدر ظاهر.
- أزلت مؤشر الماوس السابق `ns-resize`.

## الفحص
```json
{
  "base_file": "suhail_v20_verbal_samples_sprint02_arabic_digits_passage_fix.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "hard_lock_css": true,
  "hard_lock_js": false,
  "touchmove_prevents_parent_scroll": false,
  "wheel_prevents_parent_scroll": true,
  "no_cursor_indicator": true,
  "scrollbar_hidden": true,
  "arabic_digits_kept": true,
  "verbal_sample_reading_kept": true
}
```
