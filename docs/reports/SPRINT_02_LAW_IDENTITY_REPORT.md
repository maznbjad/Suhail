# Sprint 02 — هوية القوانين وشخصية سهيل

## المنفذ
- إعادة بناء كرت القانون بهوية مستقلة جديدة لتجنب تعارض CSS القديم.
- اعتماد تصميم موحد يتضمن:
  - Ribbon عنوان القانون.
  - صندوق القانون والتعريف.
  - ثلاث بطاقات لمعنى الرموز.
  - صندوق «متى أستخدمه؟».
- دمج شخصية سهيل داخل الكرت.
- وضع بندول فيزيائي في الجهة المقابلة.
- منع تداخل الشخصية والنص والزخارف.
- معالجة نوعين من القوانين:
  - القوانين النصية العربية.
  - القوانين الرمزية القصيرة والطويلة.
- تصغير القوانين الطويلة تلقائيًا.
- تصغير وصف الاستخدام تلقائيًا إذا كان طويلًا.

## التبرير
المشاكل السابقة نتجت عن تراكم عدة طبقات CSS على نفس أسماء الكلاسات.
في هذا السبرنت تم إنشاء مساحة أسماء مستقلة بالكامل تبدأ بـ `slaw2-`، وبالتالي لا تتأثر بقايا التصاميم القديمة.

## الفحص
```json
{
  "base_file": "suhail_law_identity_sprint01.zip",
  "python_compile_ok": true,
  "python_compile_error": "",
  "js_syntax_ok": true,
  "js_syntax_error": "",
  "new_namespace_isolated": true,
  "old_renderer_replaced": true,
  "new_section_wrapper": true,
  "character_asset_added": true,
  "character_loader_added": true,
  "character_inside_card": true,
  "pendulum_inside_card": true,
  "three_symbol_cards": true,
  "textual_formula_mode": true,
  "long_symbolic_formula_mode": true,
  "physics1_2_kept": true,
  "previous_fixes_kept": true
}
```
