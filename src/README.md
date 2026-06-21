# Source Modules — Sprint 47

- `core/data_loader.py` — تحميل البيانات بكاش.
- `core/asset_cache.py` — تجهيز Data URI للأصول.
- `core/learning_repository.py` — مستودع الأسئلة SQLite.
- `core/app_config.py` — إعدادات الأدمن والمزايا والشخصيات والتحديات والدرجات.
- `core/student_scoring.py` — نماذج توقع قابلة للاختبار.
- `core/challenge_repository.py` — مخطط الملف الشخصي والصداقات والتحديات.
- `ui/learning_journey.js` — رحلة Sprints 30–39.
- `ui/sprint47_experience.js` — طبقة تجربة Sprints 40–47.
- `ui/sprint47.css` — نظام تصميم الطبقة الجديدة.
- `api/server.py` — API محلي منظم للنسخة المحمولة القادمة.

يبقى `app.py` كبيرًا لأنه يحتوي إرث الواجهات السابقة. هذه المرحلة أوقفت زيادة الملف عبر عزل التطوير الجديد، لكن التفكيك الكامل يحتاج اختبارات انحدار صفحة بصفحة قبل المتجر.
