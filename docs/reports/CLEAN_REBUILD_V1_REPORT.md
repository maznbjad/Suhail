# Clean Rebuild V1 — إدارة الأسئلة من جديد

## الأساس
تم حذف الاعتماد على محاولات Sprint 01/02/03 السابقة، والبناء من جديد على:
`suhail_logo_inside_iframe_fix_v20.zip`

## سبب إعادة البناء
المشكلة السابقة كانت أن صفحة إدارة الأسئلة أُضيفت خارج منطقة `.content` في واجهة الهاتف، لذلك كانت الصفحة تفتح لكنها تظهر فارغة.  
في هذه النسخة تم إدخال صفحة إدارة الأسئلة داخل `.content` مباشرة.

## ما تم
- إضافة حسابات:
  - `User X / 123456` = مدخل بيانات
  - `User Y / 123456` = مراجع الأسئلة
- الطالب العادي لا يرى زر إدارة الأسئلة نهائيًا.
- زر إدارة الأسئلة يظهر فقط في الحسابات المصرح لها.
- صفحة إدارة الأسئلة داخل منطقة المحتوى الصحيحة.
- User X يرى:
  - رفع سؤال جديد
  - نص السؤال
  - الخيارات
  - الإجابة الصحيحة
  - صورة السؤال
  - ملاحظات
  - إرسال للمراجعة
- User Y يرى:
  - كروت المراجعة
  - الإجابة الصحيحة بالأخضر
  - قبول / رفض / تعديل
  - ملاحظات إلزامية عند الرفض أو التعديل
- Admin يرى المسارين.

## طريقة الاختبار
1. شغل التطبيق.
2. ادخل طالب عادي: لا يظهر زر إدارة الأسئلة.
3. ادخل `User X / 123456`: الحساب → إدارة الأسئلة → رفع سؤال.
4. أرسل سؤال.
5. ادخل `User Y / 123456`: الحساب → إدارة الأسئلة → مراجعة الطلبات.

## الفحص
```json
{
  "base_check": {
    "base_file": "suhail_logo_inside_iframe_fix_v20.zip",
    "has_v20_iframe_logo_fix": true,
    "has_v20_report": true,
    "has_profile_page": true,
    "has_content": true
  },
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "structural": {
    "content_idx": 1846411,
    "qmp_idx": 1865929,
    "ai_idx": 1866562,
    "qmp_after_content_start": true,
    "qmp_before_ai": true,
    "has_content_close_before_ai_after_qmp": true
  },
  "has_user_x_python": true,
  "has_user_y_python": true,
  "has_profile_entry": true,
  "student_default_hidden": true,
  "has_question_page": true,
  "has_entry_form": false,
  "has_review_form": false,
  "has_access_guard": true
}
```
