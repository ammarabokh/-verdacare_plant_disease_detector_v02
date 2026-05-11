# 🚀 دليل البدء السريع - الشات بوت

## ⚡ البدء في 3 خطوات

### 1️⃣ تأكد من التكوين
```bash
# تحقق من وجود HF_TOKEN في ملف .env
cat .env
```

يجب أن يحتوي على:
```env
HF_TOKEN=hf_your_token_here
HF_MODEL=Qwen/Qwen2.5-72B-Instruct
```

### 2️⃣ شغّل التطبيق
```bash
# تفعيل البيئة الافتراضية
.venv\Scripts\activate

# تشغيل التطبيق
python app.py
```

### 3️⃣ افتح المتصفح
```
http://localhost:5000
```

---

## ✅ اختبار سريع

```bash
# اختبار الاتصال بـ Hugging Face
python Testhuggingface.py
```

**النتيجة المتوقعة:** 5/5 اختبارات نجحت ✅

---

## 💬 تجربة الشات بوت

### من Python:
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# اسأل سؤال
response = chatbot.process_message(
    message="ما هو مرض جرب التفاح؟",
    session_id=session_id,
    lang="ar"
)

print(response)
```

### من المتصفح:
1. ارفع صورة نبات
2. انتظر التشخيص
3. اسأل الشات بوت عن المرض
4. احصل على نصائح العلاج

---

## 🔧 تغيير النموذج (اختياري)

في ملف `.env`:
```env
# نموذج أصغر وأسرع
HF_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct

# أو النموذج الافتراضي (موصى به)
HF_MODEL=Qwen/Qwen2.5-72B-Instruct
```

---

## 📚 الوثائق الكاملة

- **`FINAL_REPORT.md`** - التقرير النهائي الشامل
- **`CHATBOT_FIX_SUMMARY.md`** - تفاصيل الإصلاحات
- **`chatbot/README_CHATBOT.md`** - دليل استخدام مفصل

---

## ❓ مشاكل شائعة

### المشكلة: "HF_TOKEN is missing"
**الحل:** أضف التوكن في ملف `.env`

### المشكلة: "Model not supported"
**الحل:** استخدم النموذج الافتراضي: `Qwen/Qwen2.5-72B-Instruct`

### المشكلة: الرد بطيء
**الحل:** استخدم نموذج أصغر أو قلل `HF_MAX_TOKENS`

---

## 🎉 جاهز!

التطبيق الآن جاهز للاستخدام بنسبة 100%! 🚀

**آخر تحديث:** 2026-05-11
