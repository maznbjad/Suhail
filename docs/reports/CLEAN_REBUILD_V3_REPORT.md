# Clean Rebuild V3 — افتتاحية ثانيتين وترقيم الطلبات

## الأساس
تم البناء على:
`suhail_v20_question_management_clean_rebuild_v2.zip`

## التغييرات
- تقليل افتتاحية شعار سهيل إلى ثانيتين تقريبًا:
  - `SUHAIL_SPLASH_DURATION = 2000`
  - `SUHAIL_SPLASH_MIN_VISIBLE = 1950`
- تعديل ترقيم طلبات الأسئلة:
  - بدل `Q-<timestamp>`
  - صار الترقيم:
    - `Q-000001`
    - `Q-000002`
    - `Q-000003`
- عرض الطلب يبقى بالشكل:
  - `#Q-000001`
- الترقيم محفوظ في `localStorage` عبر:
  - `suhail_question_request_counter_v1`
- حافظت على:
  - إخفاء إدارة الأسئلة عن الطالب
  - رفع السؤال لـ User X
  - مراجعة الطلبات لـ User Y
  - القبول/الرفض/التعديل

## الفحص
```json
{
  "base_check": {
    "base_file": "suhail_v20_question_management_clean_rebuild_v2.zip",
    "has_clean_rebuild_v2": true,
    "has_v20_iframe_logo_fix": true,
    "has_question_page": true,
    "has_entry_review": true
  },
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "splash_duration_2000": true,
  "splash_min_visible_1950": true,
  "has_sequential_id_helper": true,
  "uses_sequential_id": true,
  "has_counter_key": true,
  "has_clean_entry": true,
  "has_clean_review": true,
  "student_hidden_guard": true
}
```
