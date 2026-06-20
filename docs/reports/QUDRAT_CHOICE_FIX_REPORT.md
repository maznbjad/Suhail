# Qudrat Choice Fix — اختيار كمي/لفظي قبل إعداد الاختبار

## الأساس
تم البناء على:
`suhail_v20_verbal_samples_sprint02_math_text_fix.zip`

## التعديل
- كرت **قدرات** في الرئيسية لم يعد يفتح إعداد اختبار كمي مباشرة.
- عند الضغط على **قدرات** تظهر خيارات:
  - كمي
  - لفظي
- الضغط على كمي يفتح إعداد اختبار **قدرات كمي**.
- الضغط على لفظي يفتح إعداد اختبار **قدرات لفظي**.
- كرت **تحصيلي** يفتح إعداد التحصيلي مباشرة.
- أزلت عبارة: `القسم الحالي: ...` من تحت عنوان إعداد الاختبار.
- أبقيت العبارة العامة: `اختر الأقسام ثم حدّد عدد الأسئلة.`
- أسئلة Sprint 02 اللفظية وسؤال استيعاب المقروء محفوظة.

## الفحص
```json
{
  "base_file": "suhail_v20_verbal_samples_sprint02_math_text_fix.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "home_qudrat_card_opens_choice": true,
  "choice_panel_exists": true,
  "quant_choice_exists": true,
  "verbal_choice_exists": true,
  "tahsili_card_direct_setup": true,
  "exercise_subtitle_removed_current_section": true,
  "exercise_subtitle_instruction": true,
  "verbal_sample_reading_kept": true,
  "math_text_fix_kept": true
}
```
