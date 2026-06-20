# Sprint 01 — التصنيف الذكي وأسئلة استيعاب المقروء

## الأساس
تم البناء على:
`suhail_v20_question_management_clean_rebuild_v3.zip`

## ما تم
- حذف كلمة **فتح** من أزرار إدارة الأسئلة:
  - `رفع سؤال جديد`
  - `مراجعة الطلبات`
- تحويل التصنيف من كتابة حرة إلى قائمة ذكية حسب المسار.
- إذا المسار **تحصيلي** تظهر:
  - فيزياء، كيمياء، أحياء، رياضيات
- إذا المسار **قدرات كمي** تظهر:
  - حساب، جبر، هندسة، إحصاء وتحليل بيانات، مسائل لفظية حسابية
- إذا المسار **قدرات لفظي** تظهر:
  - تناظر لفظي، استيعاب مقروء، إكمال جمل، خطأ سياقي، ارتباط واختلاف، مفردة شاذة
- إذا التصنيف **استيعاب مقروء** تظهر خانة جديدة:
  - **نص القطعة**
- نص القطعة صار يُحفظ مع السؤال.
- في مراجعة User Y يظهر نص القطعة داخل مربع منفصل قابل للتمرير.
- في عرض الطالب، مربع نص القطعة ثابت الارتفاع وقابل للتمرير داخليًا بدون تحريك الصفحة بالكامل.

## الفحص
```json
{
  "base_check": {
    "base_file": "suhail_v20_question_management_clean_rebuild_v3.zip",
    "has_clean_rebuild_v3": true,
    "has_qm_js": true,
    "has_entry": true,
    "has_review": true,
    "splash_2_sec": true,
    "sequential_ids": true
  },
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "removed_fath_buttons": true,
  "has_dynamic_category_map": true,
  "category_is_select": true,
  "has_tahsili_subjects": true,
  "has_verbal_categories": true,
  "has_quant_categories": true,
  "has_reading_passage_field": true,
  "requires_reading_passage": true,
  "stores_passage": true,
  "review_shows_passage": true,
  "student_passage_scroll_box": true
}
```
