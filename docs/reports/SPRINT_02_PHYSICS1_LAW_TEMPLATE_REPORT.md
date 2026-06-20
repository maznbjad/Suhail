# Sprint 02 — قالب قوانين فيزياء 1

## الأساس
تم البناء على:
`suhail_v20_verbal_samples_sprint02_passage_lock_fix.zip`

## المنفذ
- تم تطبيق قالب القوانين الجديد على قوانين **فيزياء 1** داخل الملخصات.
- كل قانون في فيزياء 1 صار يعرض بهذا الترتيب:
  1. شريط عنوان القانون
  2. صندوق المعادلة
  3. تعريف مختصر
  4. معنى الرموز
  5. متى أستخدمه؟
- تم الحفاظ على أن القالب يعمل على فيزياء 1 فقط في هذا السبرنت.
- عدد قوانين فيزياء 1 المكتشفة من البيانات الحالية: **34 قانون**.
- تم تغيير الكرت القديم من "القوانين والقاعدة" إلى "قاعدة الوحدة المختصرة" حتى لا يتعارض مع القالب الجديد.
- بقيت إصلاحات النسخة السابقة محفوظة:
  - أرقام القدرات بالعربي
  - حذف الانتقال إلى الملخص بعد النتيجة
  - تثبيت سكرول استيعاب المقروء

## طريقة التجربة
1. شغّل `app.py`.
2. ادخل الملخصات.
3. اختر تحصيلي → فيزياء → فيزياء 1.
4. افتح أي وحدة.
5. انزل إلى قسم **القوانين والقاعدة**.

## الفحص
```json
{
  "base_file": "suhail_v20_verbal_samples_sprint02_passage_lock_fix.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "law_template_css_added": true,
  "law_template_renderer_added": true,
  "physics1_only_renderer_condition": true,
  "new_law_section_title": true,
  "old_law_card_renamed": true,
  "physics1_formula_count_detected": 34,
  "sample_law_period_time": true,
  "symbol_meaning_cards": true,
  "when_to_use_box": true,
  "adult_student_icon": true,
  "previous_passage_lock_kept": true,
  "arabic_digits_kept": true
}
```
