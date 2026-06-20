# Sprint 02 — إضافة أسئلة لفظي تجريبية للبنك

## الأساس
تم البناء على:
`suhail_v20_verbal_question_fields_sprint01_symbols_bigger_fix.zip`

## ما تم
أضفت إلى `questions.json` مجموعة أسئلة لفظي تجريبية من 8 أسئلة.

## التوزيع
- استيعاب مقروء: 1 سؤال
- تناظر لفظي: 2 سؤال
- إكمال جمل: 2 سؤال
- خطأ سياقي: 1 سؤال
- ارتباط واختلاف: 1 سؤال
- مفردة شاذة: 1 سؤال

## سؤال استيعاب المقروء
المعرّف:
`VERB-S02-000001`

هذا السؤال يحتوي على:
- `passage`
- `reading`
- `passageText`

حتى يظهر نص القطعة في مربع مستقل قابل للتمرير داخل الاختبار.

## طريقة التجربة
1. افتح التطبيق.
2. اختر **قدرات لفظي**.
3. اختر كل التصنيفات.
4. اضغط ابدأ الاختبار.
5. اختر **أسئلة جديدة**.
6. سيظهر ضمن الأسئلة سؤال **استيعاب مقروء**، وإذا لم يظهر أولًا اضغط التالي.

## الفحص
```json
{
  "base_file": "suhail_v20_verbal_question_fields_sprint01_symbols_bigger_fix.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "questions_json_count": 8,
  "sample_verbal_count": 8,
  "has_reading_question": true,
  "reading_question_id": "VERB-S02-000001",
  "all_samples_have_choices": true,
  "all_samples_have_correct": true,
  "keeps_question_management": true,
  "keeps_passage_display": true,
  "keeps_symbols_bigger": true
}
```
