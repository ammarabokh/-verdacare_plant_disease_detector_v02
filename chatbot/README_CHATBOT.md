# 🤖 دليل استخدام الشات بوت الزراعي

## 📖 نظرة عامة

الشات بوت الزراعي هو مساعد ذكي يساعد المزارعين في:
- 💬 الإجابة على الأسئلة الزراعية
- 🌱 تقديم نصائح حول أمراض النباتات
- 💊 اقتراح العلاجات والوقاية
- 📚 توفير معلومات من قاعدة المعرفة المحلية

---

## 🎯 الميزات الرئيسية

### 1. دعم ثنائي اللغة
- ✅ العربية (اللغة الافتراضية)
- ✅ الإنجليزية

### 2. ذاكرة المحادثة
- يتذكر آخر 10 رسائل من المحادثة
- يفهم السياق من التشخيص السابق
- ينتهي الجلسة تلقائياً بعد 30 دقيقة من عدم النشاط

### 3. مصادر المعلومات
- **قاعدة المعرفة المحلية:** للإجابات السريعة عن الأمراض المعروفة
- **نموذج AI (Qwen 2.5):** للأسئلة العامة والمعقدة
- **Fallback:** إذا فشل الاتصال بالـ AI، يستخدم قاعدة المعرفة المحلية

### 4. Streaming
- الردود تظهر بشكل تدريجي (كتابة حية)
- تجربة مستخدم أفضل وأسرع

---

## 🔧 التكوين

### متغيرات البيئة (.env)

```env
# Hugging Face API Token (مطلوب)
HF_TOKEN=hf_your_token_here

# النموذج المستخدم (اختياري - القيمة الافتراضية: Qwen/Qwen2.5-72B-Instruct)
HF_MODEL=Qwen/Qwen2.5-72B-Instruct
```

### إعدادات Config (config.py)

```python
# Hugging Face
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # النموذج الافتراضي
HF_MAX_TOKENS = 500                      # الحد الأقصى للرموز في الرد
HF_TEMPERATURE = 0.7                     # درجة الإبداع (0.0 - 1.0)
```

---

## 📁 هيكل الملفات

```
chatbot/
├── chatbot_logic.py        # المنطق الرئيسي للشات بوت
├── huggingface_client.py   # عميل الاتصال بـ Hugging Face
├── chat_memory.py          # إدارة ذاكرة المحادثات
└── knowledge_base.json     # قاعدة المعرفة المحلية
```

---

## 🚀 كيفية الاستخدام

### 1. من خلال التطبيق (Flask)

```python
from chatbot.chatbot_logic import chatbot

# معالجة رسالة
response = chatbot.process_message(
    message="ما هو مرض جرب التفاح؟",
    session_id="user_session_123",
    lang="ar",
    context="جرب التفاح"  # اختياري: السياق من التشخيص
)

print(response)
```

### 2. مباشرة من Python

```python
from chatbot.huggingface_client import HuggingFaceClient

client = HuggingFaceClient()

# رد عادي
response = client.generate_response(
    prompt="ما هي الطماطم؟",
    system_prompt="أنت خبير زراعي. أجب بالعربية."
)

# رد مع streaming
for chunk in client.generate_stream(
    prompt="كيف أعالج مرض البياض الدقيقي؟",
    system_prompt="أنت خبير زراعي. أجب بالعربية."
):
    print(chunk, end='', flush=True)
```

### 3. عبر API (من التطبيق)

```javascript
// إرسال رسالة
fetch('/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: 'ما هو مرض جرب التفاح؟'
    })
})
.then(response => response.json())
.then(data => {
    console.log(data.response);
});

// مسح المحادثة
fetch('/chat/clear', {
    method: 'POST'
});
```

---

## 🧪 الاختبار

### اختبار شامل

```bash
python Testhuggingface.py
```

**النتيجة المتوقعة:**
```
✅ التوكن               نجح
✅ المكتبات             نجح
✅ عميل HF              نجح
✅ رد النموذج           نجح
✅ Chatbot Logic        نجح
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
النتيجة: 5/5 اختبارات نجحت ✅
```

### اختبار يدوي

```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# اختبار 1: سؤال عام
response1 = chatbot.process_message(
    "ما هي الطماطم؟",
    session_id,
    "ar"
)
print("الرد 1:", response1)

# اختبار 2: سؤال عن مرض (من قاعدة المعرفة)
response2 = chatbot.process_message(
    "ما هو مرض جرب التفاح؟",
    session_id,
    "ar"
)
print("الرد 2:", response2)

# اختبار 3: سؤال مع سياق
response3 = chatbot.process_message(
    "ما العلاج؟",
    session_id,
    "ar",
    context="جرب التفاح"
)
print("الرد 3:", response3)
```

---

## 🔍 آلية العمل

### تدفق معالجة الرسالة:

```
1. استقبال الرسالة من المستخدم
   ↓
2. التحقق من السياق (context)
   ↓
3. البحث في قاعدة المعرفة المحلية
   ├─ إذا وُجدت → إرجاع الرد مباشرة ✅
   └─ إذا لم توجد → الانتقال للخطوة 4
   ↓
4. إرسال الطلب إلى Hugging Face API
   ├─ نجح → إرجاع الرد ✅
   └─ فشل → محاولة الرد من قاعدة المعرفة (fallback)
   ↓
5. حفظ الرسالة والرد في الذاكرة
   ↓
6. إرجاع الرد للمستخدم
```

### مثال على التدفق:

**سيناريو 1: سؤال عن مرض معروف**
```
المستخدم: "ما هو مرض جرب التفاح؟"
         ↓
قاعدة المعرفة: ✅ وُجد المرض
         ↓
الرد: معلومات مفصلة من قاعدة المعرفة
```

**سيناريو 2: سؤال عام**
```
المستخدم: "كيف أحسن جودة التربة؟"
         ↓
قاعدة المعرفة: ❌ لم يُوجد
         ↓
Hugging Face API: ✅ نجح
         ↓
الرد: نصائح من نموذج AI
```

**سيناريو 3: سؤال مع سياق**
```
المستخدم: "ما العلاج؟"
السياق: "جرب التفاح"
         ↓
قاعدة المعرفة: ✅ وُجد المرض في السياق
         ↓
الرد: معلومات العلاج من قاعدة المعرفة
```

---

## ⚙️ التخصيص

### تغيير النموذج

في ملف `.env`:
```env
HF_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
```

أو في `config.py`:
```python
HF_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"
```

### تعديل System Prompt

في `chatbot_logic.py` → `_build_system_prompt()`:
```python
base_prompts = {
    'ar': """أنت مساعد زراعي خبير. ساعد المزارعين في:
- تشخيص أمراض النباتات
- نصائح العلاج والوقاية
- الممارسات الزراعية الجيدة

كن مختصرًا وعمليًا. أجب باللغة العربية.""",
    # ...
}
```

### تعديل إعدادات الذاكرة

في `chat_memory.py`:
```python
chat_memory = ChatMemory(
    max_history=10,        # عدد الرسائل المحفوظة
    expiry_minutes=30      # مدة انتهاء الجلسة
)
```

### إضافة أمراض جديدة

في `knowledge_base.json`:
```json
{
  "diseases": {
    "Disease_Name": {
      "ar": {
        "name": "اسم المرض بالعربية",
        "description": "وصف المرض",
        "symptoms": "الأعراض",
        "treatment": "العلاج",
        "prevention": "الوقاية",
        "products": ["منتج 1", "منتج 2"]
      },
      "en": {
        "name": "Disease Name in English",
        // ...
      }
    }
  }
}
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: "HF_TOKEN is missing"
**الحل:**
1. تأكد من وجود ملف `.env` في المجلد الرئيسي
2. تأكد من أن `HF_TOKEN` موجود في الملف
3. احصل على token من: https://huggingface.co/settings/tokens

### المشكلة: "Model not supported"
**الحل:**
1. تأكد من أن النموذج صحيح في `.env` أو `config.py`
2. جرب النموذج الافتراضي: `Qwen/Qwen2.5-72B-Instruct`
3. تحقق من أن النموذج متاح على Hugging Face

### المشكلة: "Rate limit exceeded"
**الحل:**
1. انتظر بضع دقائق قبل المحاولة مرة أخرى
2. قلل عدد الطلبات
3. فكر في الترقية لحساب PRO

### المشكلة: الرد بطيء
**الحل:**
1. استخدم نموذج أصغر: `Qwen/Qwen2.5-Coder-32B-Instruct`
2. قلل `HF_MAX_TOKENS` في `config.py`
3. تأكد من سرعة الإنترنت

### المشكلة: الرد ليس بالعربية
**الحل:**
1. تأكد من أن `lang='ar'` في `process_message()`
2. تحقق من System Prompt في `chatbot_logic.py`
3. جرب إضافة "أجب بالعربية" في السؤال

---

## 📊 الأداء

### معدلات الاستجابة:
- **قاعدة المعرفة المحلية:** < 100ms ⚡
- **Hugging Face API (عادي):** 2-5 ثواني 🚀
- **Hugging Face API (streaming):** يبدأ فوراً ⚡

### استهلاك الموارد:
- **الذاكرة:** ~50MB (بدون TensorFlow)
- **الشبكة:** ~1-5KB لكل طلب
- **CPU:** منخفض جداً

---

## 🔐 الأمان

### حماية Token:
- ✅ لا تشارك `HF_TOKEN` مع أحد
- ✅ لا ترفع ملف `.env` إلى Git
- ✅ استخدم `.gitignore` لاستبعاد `.env`

### حماية البيانات:
- ✅ الذاكرة في الـ RAM فقط (لا تُحفظ في قاعدة بيانات)
- ✅ الجلسات تنتهي تلقائياً بعد 30 دقيقة
- ✅ لا يتم إرسال معلومات حساسة إلى Hugging Face

---

## 📈 التطوير المستقبلي

### ميزات مقترحة:
- [ ] دعم الصور في الشات (Vision models)
- [ ] تكامل مع WhatsApp/Telegram
- [ ] تحليل المشاعر (Sentiment Analysis)
- [ ] توصيات مخصصة بناءً على الموقع
- [ ] دعم الصوت (Speech-to-Text)
- [ ] Multi-turn conversations أفضل
- [ ] Caching للأسئلة المتكررة
- [ ] Analytics dashboard

---

## 🤝 المساهمة

إذا كنت تريد تحسين الشات بوت:

1. أضف أمراض جديدة في `knowledge_base.json`
2. حسّن System Prompts في `chatbot_logic.py`
3. أضف اختبارات جديدة في `Testhuggingface.py`
4. شارك ملاحظاتك وأفكارك!

---

## 📞 الدعم

إذا واجهت مشاكل:
1. راجع قسم "استكشاف الأخطاء" أعلاه
2. شغّل `python Testhuggingface.py` للتشخيص
3. تحقق من ملف `CHATBOT_FIX_SUMMARY.md`

---

## 📄 الترخيص

هذا المشروع جزء من نظام تشخيص أمراض النباتات.

---

**آخر تحديث:** 2026-05-11  
**الإصدار:** 2.0 (بعد الإصلاح)  
**الحالة:** ✅ يعمل بشكل كامل
