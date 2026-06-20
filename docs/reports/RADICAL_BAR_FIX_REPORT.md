# Radical Bar Fix — الجذر بمظلة بدون أقواس

## الأساس
تم البناء على:
`suhail_v20_verbal_question_fields_sprint01_sqrt_fix.zip`

## التعديل
- زر الجذر صار: `√x̅`
- إذا كتبت `20` ثم ضغطت الجذر، يصير:
  - `√2̅0̅`
- إذا ظللت `20` ثم ضغطت الجذر، يصير:
  - `√2̅0̅`
- أزلت صيغة الأقواس:
  - لم يعد يكتب `√(20)`
- إذا ضغطت الجذر بدون رقم، يضيف `√` فقط وتكمل بعده.

## الفحص
```json
{
  "base_check": {
    "base_file": "suhail_v20_verbal_question_fields_sprint01_sqrt_fix.zip",
    "has_sqrt_fix": true,
    "has_math_box": true,
    "has_verbal_fields": true
  },
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "sqrt_button_radical_bar_label": true,
  "has_radical_text_helper": true,
  "wraps_previous_number_as_radical": true,
  "no_sqrt_parentheses_branch": true,
  "uses_combining_overline": true,
  "fallback_is_sqrt_only": true,
  "keeps_math_box": true,
  "keeps_verbal_fields": true
}
```
