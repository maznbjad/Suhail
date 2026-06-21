# Suhail Sprint 55 — هيكل المشروع

## التشغيل

- `app.py` — واجهة Streamlit الحالية ومجمّع الصفحات القديمة والطبقة النهائية.
- `run_suhail.bat` — تشغيل الواجهة محليًا على ويندوز مع حسابات التطوير فقط.
- `run_api.bat` — تشغيل API المحلي عبر Waitress.

## واجهة المستخدم

- `src/ui/learning_journey.js` — أساس رحلة Sprints 30–39.
- `src/ui/sprint47_experience.js` و`sprint47.css` — طبقة المرحلة السابقة المحفوظة للتوافق.
- `src/ui/sprint54_experience.js` — المالك النهائي للرئيسية والتنقل والملف والقياسين والستريك والأدمن والتحديات.
- `src/ui/sprint54.css` — نظام التصميم النهائي وقواعد Main/Summary/Exam/Auth.
- `src/ui/sprint55_account.js` — صفحة الحساب المجمعة والصفحات الداخلية التابعة لها.
- `src/ui/sprint55_account.css` — تصميم الحساب المرجعي، صفوف الإعدادات، الوضع الداكن، والتذييل.

## النواة

- `src/core/data_loader.py` — تحميل JSON بكاش.
- `src/core/asset_cache.py` — أصول Data URI بكاش لنسخة Streamlit.
- `src/core/learning_repository.py` — مستودع بنك الأسئلة SQLite.
- `src/core/app_config.py` — تحميل الإعدادات المركزية.
- `src/core/student_scoring.py` — نماذج مؤشر الجاهزية؛ التحصيلي موحد ولا يستخدم المسار.
- `src/core/auth_repository.py` — حسابات PBKDF2 وتوكنات API.
- `src/core/challenge_repository.py` — مخطط الملف، القياسات، النشاط، الصداقات والتحديات.

## البيانات

- `data/questions.json` — 1000 سؤال تطوير غير مؤهل للنشر.
- `data/suhail_learning.db` — الأسئلة وجداول الحسابات والقياسات والنشاط والأصدقاء والتحديات.
- `data/admin/admin_settings.json` — إعدادات الرحلة والقياس والستريك والتحديات والأداء.
- `data/admin/feature_flags.json` — مفاتيح Sprint 54.
- `data/admin/content_workflow.json` — صلاحيات ومسار اعتماد المحتوى.
- `data/avatars/avatars.json` — 8 شخصيات.
- `data/challenges/challenge_templates.json` — قوالب التحديات.
- `data/scoring/score_models.json` — قدرات علمي/أدبي + تحصيلي موحد.
- `data/users.json` — فارغ في الحزمة؛ لا توجد كلمات مرور نصية للإنتاج.

## الأصول

- `assets/avatars/` — 8 شخصيات SVG خفيفة.
- `assets/runtime/` — أصول WebP المستخدمة أثناء التشغيل.
- `assets/source/` — المصادر الأصلية.
- `assets/brand/` — هوية سهيل.
- `assets/images/splash/` — افتتاحية 3 ثوانٍ.

## API

- `src/api/server.py` — حسابات، ملف الطالب، قياسان مستقلان، نشاط/ستريك، أسئلة، ملخصات، أصدقاء، تحديات، وإعدادات أدمن محمية.

## الفحص والتوثيق

- `scripts/validate_project.py` — المدخل الرئيسي للفحص.
- `scripts/validate_sprint54.py` — فحص تفصيلي مع API مؤقت دون تلويث قاعدة التسليم.
- `scripts/audit_question_bank.py` — تدقيق وإصلاحات بنك التطوير.
- `docs/reports/SPRINT_48_54_IMPLEMENTATION_REPORT.md`
- `docs/reports/SPRINT_54_ARCHITECTURE_AND_LIMITS.md`
- `docs/reports/SPRINT_54_CHECKS.json`
- `docs/reports/SPRINT_54_VISUAL_QA.json`
- `docs/reports/SPRINT_55_ACCOUNT_PAGE_REPORT.md`
- `docs/reports/SPRINT_55_CHECKS.json`
