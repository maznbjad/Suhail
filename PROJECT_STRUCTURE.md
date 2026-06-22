# Suhail Sprint 59 — هيكل المشروع

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
- `src/ui/sprint56_global_theme.css` — ألوان الوضع الداكن الشامل لجميع الصفحات القديمة والجديدة.
- `src/ui/sprint56_global_theme.js` — تهيئة المظهر مبكرًا، حفظ الاختيار، وتحديث لون النظام.
- `src/ui/sprint59_summaries_navigation.js` — المالك النهائي لبوابة الملخصات، ترتيب المسارات، تفاصيل الوحدات، البحث، سلوك القائمة، وأيقونة العودة.
- `src/ui/sprint59_summaries_navigation.css` — تصميم بوابة الملخصات والمواد والوحدات والتفاصيل مع دعم الوضع الداكن.

## النواة

- `src/core/data_loader.py` — تحميل JSON بكاش.
- `src/core/asset_cache.py` — أصول Data URI بكاش لنسخة Streamlit.
- `src/core/learning_repository.py` — مستودع بنك الأسئلة SQLite.
- `src/core/app_config.py` — تحميل الإعدادات المركزية.
- `src/core/student_scoring.py` — نماذج مؤشر الجاهزية؛ التحصيلي موحد ولا يستخدم المسار.
- `src/core/auth_repository.py` — حسابات PBKDF2 وتوكنات API.
- `src/core/challenge_repository.py` — مخطط الملف، القياسات، النشاط، الصداقات والتحديات.

## البيانات

- `data/questions.json` — بنك القدرات المحوسب النشط من 280 سؤالًا، مع إبقاء بنك التطوير السابق داخل `data/archive/`.
- `data/suhail_learning.db` — الأسئلة وجداول الحسابات والقياسات والنشاط والأصدقاء والتحديات.
- `data/admin/admin_settings.json` — إعدادات الرحلة والقياس والستريك والتحديات والأداء.
- `data/admin/feature_flags.json` — مفاتيح Sprint 54.
- `data/admin/content_workflow.json` — صلاحيات ومسار اعتماد المحتوى.
- `data/avatars/avatars.json` — كتالوج 8 شخصيات مصنفة حسب نوع الحساب، مع مسارات قصّات card/avatar/half/full.
- `data/challenges/challenge_templates.json` — قوالب التحديات.
- `data/scoring/score_models.json` — قدرات علمي/أدبي + تحصيلي موحد.
- `data/users.json` — فارغ في الحزمة؛ لا توجد كلمات مرور نصية للإنتاج.

## الأصول

- `assets/avatars/generated/` — 32 أصل WebP محسّنًا: أربع قصّات لكل واحدة من الشخصيات الثماني.
- `assets/runtime/` — أصول WebP المستخدمة أثناء التشغيل.
- `assets/source/` — المصادر الأصلية.
- `assets/brand/` — هوية سهيل.
- `assets/images/splash/` — افتتاحية 3 ثوانٍ.

## API

- `src/api/server.py` — حسابات، ملف الطالب، قياسان مستقلان، نشاط/ستريك، أسئلة، ملخصات، أصدقاء، تحديات، وإعدادات أدمن محمية.

## الفحص والتوثيق

- `scripts/validate_project.py` — المدخل الرئيسي لفحص Sprint 59.
- `scripts/validate_sprint59.py` — فحص تقسيم الملخصات، منع الخلط، القائمة السفلية، أيقونة العودة، والبحث.
- `scripts/validate_sprint57.py` — فحص كتالوج الشخصيات، الأصول، فصل الجنسين، التسجيل، والـAPI.
- `scripts/validate_sprint56.py` — فحص حقن المظهر، التخزين، البنية، وملفات QA.
- `scripts/validate_sprint54.py` — فحص تفصيلي مع API مؤقت دون تلويث قاعدة التسليم.
- `scripts/audit_question_bank.py` — تدقيق وإصلاحات بنك التطوير.
- `docs/reports/SPRINT_48_54_IMPLEMENTATION_REPORT.md`
- `docs/reports/SPRINT_54_ARCHITECTURE_AND_LIMITS.md`
- `docs/reports/SPRINT_54_CHECKS.json`
- `docs/reports/SPRINT_54_VISUAL_QA.json`
- `docs/reports/SPRINT_55_ACCOUNT_PAGE_REPORT.md`
- `docs/reports/SPRINT_55_CHECKS.json`

- `docs/reports/SPRINT_57_CHARACTER_SYSTEM.md` — تقرير نظام الشخصيات الرسمية.
- `docs/reports/SPRINT_57_CHECKS.json` — نتائج فحص Sprint 57.

- `docs/reports/SPRINT_59_SUMMARIES_NAVIGATION_REPORT.md` — تقرير إصلاح الملخصات والتنقل.
- `docs/reports/SPRINT_59_CHECKS.json` — نتائج فحص Sprint 59.

### Sprint 61
- `src/ui/sprint60_summary_cleanup.css`: تحسين تباين الوضع الداكن وتوحيد حالات الأقسام غير المنشورة.
- `docs/reports/SPRINT_60_SUMMARY_CLEANUP_REPORT.md`: تقرير التنفيذ.
- `docs/reports/SPRINT_60_CHECKS.json`: نتائج الفحص.
