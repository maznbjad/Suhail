# Math Box Fix — تعديلات ما قبل Sprint 02

## الأساس
تم البناء على:
`suhail_v20_verbal_question_fields_sprint01.zip`

## ما تم
- تصغير وصف بطاقتي إدارة الأسئلة درجتين:
  - خاص بمدخل البيانات...
  - خاص بالمراجع...
- إضافة بوكس صغير باسم **المعادلات** داخل شاشة رفع السؤال.
- البوكس لا يزعج الواجهة: يفتح كشريط صغير عند الضغط.
- الرموز المضافة:
  - تربيع `x²`
  - تكعيب `x³`
  - جذر `√()`
  - كسر اعتيادي `()/()`
  - أقواس `()`
  - ضرب `×`
  - قسمة `÷`
  - زائد/ناقص `±`
  - أصغر/أكبر أو يساوي `≤` `≥`
  - باي `π`
- الإضافة تتم في مكان المؤشر داخل الحقل الحالي.
- لو ظللت نصًا ثم ضغطت:
  - تربيع: يحولها مثل `20²`
  - جذر: يحولها مثل `√(20)`
  - أقواس: يحولها مثل `(20)`
- يعمل على:
  - نص السؤال
  - نص القطعة
  - الخيارات
  - الملاحظات

## الفحص
```json
{
  "base_file": "suhail_v20_verbal_question_fields_sprint01.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "subtitle_font_reduced": true,
  "has_math_box_css": true,
  "has_math_box_js": true,
  "has_toggle_equations": true,
  "tracks_active_field": true,
  "adds_square_cube_sqrt_fraction": true,
  "options_have_focus_tracking": true,
  "question_has_focus_tracking": true,
  "keeps_verbal_fields": true,
  "keeps_2sec_splash": true,
  "keeps_sequential_ids": true
}
```
