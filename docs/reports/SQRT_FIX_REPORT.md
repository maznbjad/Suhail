# Sqrt Fix — توضيح الجذر وإدخال الرقم داخله

## الأساس
تم البناء على:
`suhail_v20_verbal_question_fields_sprint01_mathbox_fix.zip`

## التعديل
- غيرت زر الجذر من `√` إلى `√(x)` عشان يكون أوضح.
- إذا ظللت رقمًا ثم ضغطت الجذر:
  - `20` تصبح `√(20)`
- إذا كان المؤشر بعد رقم مباشرة ثم ضغطت الجذر:
  - `20` تصبح تلقائيًا `√(20)` بدون تحديد الرقم.
- إذا ضغطت الجذر بدون رقم:
  - يضيف `√()` والمؤشر يكون داخل القوس.

## الفحص
```json
{
  "base_check": {
    "base_file": "suhail_v20_verbal_question_fields_sprint01_mathbox_fix.zip",
    "has_math_box": true,
    "has_verbal_fields": true,
    "has_question_management": true
  },
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "sqrt_button_clear": true,
  "wrap_previous_number_helper": true,
  "sqrt_wraps_selected": true,
  "sqrt_wraps_previous_number": true,
  "fallback_cursor_inside_sqrt": true,
  "keeps_math_box": true,
  "keeps_verbal_fields": true
}
```
