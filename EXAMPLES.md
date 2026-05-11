# 💡 أمثلة عملية لاستخدام الشات بوت

## 📝 أمثلة Python

### مثال 1: سؤال بسيط
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

response = chatbot.process_message(
    message="ما هي الطماطم؟",
    session_id=session_id,
    lang="ar"
)

print(response)
```

**النتيجة المتوقعة:**
```
الطماطم هي نوع من النباتات التي تنتمي إلى الفصيلة الباذنجانية...
```

---

### مثال 2: سؤال عن مرض (من قاعدة المعرفة)
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

response = chatbot.process_message(
    message="ما هو مرض جرب التفاح؟",
    session_id=session_id,
    lang="ar"
)

print(response)
```

**النتيجة المتوقعة:**
```
**جرب التفاح**

الوصف: مرض فطري يصيب أشجار التفاح بسبب الفطر Venturia inaequalis...
الأعراض: بقع زيتونية داكنة على الأوراق، تشققات على الثمار...
العلاج: رش مبيدات تحتوي على الكبريت، إزالة الأوراق المصابة...
```

---

### مثال 3: محادثة متعددة الأدوار
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# السؤال الأول
response1 = chatbot.process_message(
    message="ما هو مرض البياض الدقيقي؟",
    session_id=session_id,
    lang="ar"
)
print("الرد 1:", response1[:100], "...")

# السؤال الثاني (يتذكر السياق)
response2 = chatbot.process_message(
    message="كيف أعالجه؟",
    session_id=session_id,
    lang="ar"
)
print("الرد 2:", response2[:100], "...")

# السؤال الثالث
response3 = chatbot.process_message(
    message="ما هي المنتجات الموصى بها؟",
    session_id=session_id,
    lang="ar"
)
print("الرد 3:", response3[:100], "...")
```

---

### مثال 4: استخدام السياق من التشخيص
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# المستخدم قام بتشخيص صورة وحصل على "جرب التفاح"
context = "جرب التفاح"

# الآن يسأل عن العلاج
response = chatbot.process_message(
    message="ما العلاج؟",
    session_id=session_id,
    lang="ar",
    context=context
)

print(response)
```

**النتيجة:** سيفهم الشات بوت أن السؤال عن علاج جرب التفاح

---

### مثال 5: استخدام Streaming
```python
from chatbot.huggingface_client import HuggingFaceClient

client = HuggingFaceClient()

print("السؤال: ما هي أفضل طرق الوقاية من أمراض النباتات؟")
print("الرد: ", end="", flush=True)

for chunk in client.generate_stream(
    prompt="ما هي أفضل طرق الوقاية من أمراض النباتات؟",
    system_prompt="أنت خبير زراعي. أجب بالعربية بشكل مختصر."
):
    print(chunk, end="", flush=True)

print("\n")
```

**النتيجة:** الرد يظهر كلمة بكلمة (تجربة أفضل للمستخدم)

---

### مثال 6: مسح المحادثة
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# محادثة
response1 = chatbot.process_message("مرحبا", session_id, "ar")
response2 = chatbot.process_message("ما هي الطماطم؟", session_id, "ar")

# مسح المحادثة
chatbot.clear_conversation(session_id)

# الآن الشات بوت لا يتذكر المحادثة السابقة
response3 = chatbot.process_message("ماذا قلت قبل قليل؟", session_id, "ar")
print(response3)  # لن يتذكر
```

---

### مثال 7: استخدام مع اللغة الإنجليزية
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

response = chatbot.process_message(
    message="What is tomato blight?",
    session_id=session_id,
    lang="en"
)

print(response)
```

---

### مثال 8: معالجة الأخطاء
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

try:
    response = chatbot.process_message(
        message="ما هو مرض X؟",
        session_id=session_id,
        lang="ar"
    )
    print("الرد:", response)
except Exception as e:
    print(f"حدث خطأ: {e}")
    # يمكنك هنا إضافة fallback response
    print("عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.")
```

---

## 🌐 أمثلة API (من JavaScript)

### مثال 1: إرسال رسالة
```javascript
async function sendMessage(message) {
    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    });
    
    const data = await response.json();
    console.log('الرد:', data.response);
    return data.response;
}

// استخدام
sendMessage('ما هو مرض جرب التفاح؟');
```

---

### مثال 2: مسح المحادثة
```javascript
async function clearChat() {
    const response = await fetch('/chat/clear', {
        method: 'POST'
    });
    
    const data = await response.json();
    console.log('تم مسح المحادثة:', data.status);
}

// استخدام
clearChat();
```

---

### مثال 3: محادثة كاملة
```javascript
async function chatConversation() {
    // السؤال الأول
    let response1 = await sendMessage('ما هو مرض البياض الدقيقي؟');
    console.log('الرد 1:', response1);
    
    // السؤال الثاني (مع السياق)
    let response2 = await sendMessage('كيف أعالجه؟');
    console.log('الرد 2:', response2);
    
    // مسح المحادثة
    await clearChat();
}

chatConversation();
```

---

## 🧪 أمثلة اختبار

### اختبار 1: التحقق من الاتصال
```python
from chatbot.huggingface_client import HuggingFaceClient

try:
    client = HuggingFaceClient()
    response = client.generate_response(
        prompt="Hi",
        system_prompt="Reply with one word."
    )
    print("✅ الاتصال يعمل:", response)
except Exception as e:
    print("❌ الاتصال فشل:", e)
```

---

### اختبار 2: التحقق من دعم العربية
```python
from chatbot.huggingface_client import HuggingFaceClient

client = HuggingFaceClient()
response = client.generate_response(
    prompt="ما هي الطماطم؟ أجب بكلمة واحدة",
    system_prompt="أنت خبير زراعي. أجب بالعربية."
)

if any(ord(c) > 127 for c in response):  # يحتوي على أحرف عربية
    print("✅ دعم العربية يعمل:", response)
else:
    print("⚠️ الرد ليس بالعربية:", response)
```

---

### اختبار 3: التحقق من قاعدة المعرفة
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

# اسأل عن مرض موجود في قاعدة المعرفة
response = chatbot.process_message(
    message="ما هو مرض جرب التفاح؟",
    session_id=session_id,
    lang="ar"
)

# يجب أن يحتوي الرد على معلومات من قاعدة المعرفة
if "جرب التفاح" in response and "Venturia inaequalis" in response:
    print("✅ قاعدة المعرفة تعمل")
else:
    print("⚠️ قد تكون هناك مشكلة في قاعدة المعرفة")
```

---

## 🎯 سيناريوهات استخدام حقيقية

### سيناريو 1: مزارع يشخص مرض
```python
from chatbot.chatbot_logic import chatbot
import uuid

# المزارع يرفع صورة ويحصل على تشخيص
diagnosis = "جرب التفاح"
confidence = 0.95

# إنشاء جلسة
session_id = str(uuid.uuid4())

# السؤال الأول: ما هذا المرض؟
response1 = chatbot.process_message(
    message="ما هو هذا المرض؟",
    session_id=session_id,
    lang="ar",
    context=diagnosis
)
print("المزارع: ما هو هذا المرض؟")
print(f"الشات بوت: {response1}\n")

# السؤال الثاني: كيف أعالجه؟
response2 = chatbot.process_message(
    message="كيف أعالجه؟",
    session_id=session_id,
    lang="ar",
    context=diagnosis
)
print("المزارع: كيف أعالجه؟")
print(f"الشات بوت: {response2}\n")

# السؤال الثالث: ما المنتجات الموصى بها؟
response3 = chatbot.process_message(
    message="ما المنتجات الموصى بها؟",
    session_id=session_id,
    lang="ar",
    context=diagnosis
)
print("المزارع: ما المنتجات الموصى بها؟")
print(f"الشات بوت: {response3}\n")
```

---

### سيناريو 2: مزارع يسأل أسئلة عامة
```python
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

questions = [
    "كيف أحسن جودة التربة؟",
    "ما هي أفضل أوقات الري؟",
    "كيف أحمي نباتاتي من الآفات؟"
]

for question in questions:
    response = chatbot.process_message(
        message=question,
        session_id=session_id,
        lang="ar"
    )
    print(f"السؤال: {question}")
    print(f"الرد: {response[:150]}...\n")
```

---

## 📊 قياس الأداء

### قياس وقت الاستجابة
```python
import time
from chatbot.chatbot_logic import chatbot
import uuid

session_id = str(uuid.uuid4())

start_time = time.time()
response = chatbot.process_message(
    message="ما هو مرض جرب التفاح؟",
    session_id=session_id,
    lang="ar"
)
end_time = time.time()

print(f"وقت الاستجابة: {end_time - start_time:.2f} ثانية")
print(f"طول الرد: {len(response)} حرف")
```

---

## 🔧 تخصيص متقدم

### تخصيص System Prompt
```python
from chatbot.huggingface_client import HuggingFaceClient

client = HuggingFaceClient()

custom_prompt = """أنت خبير زراعي متخصص في أمراض الطماطم.
أجب بشكل مختصر وعملي.
استخدم اللغة العربية الفصحى."""

response = client.generate_response(
    prompt="ما هي أمراض الطماطم الشائعة؟",
    system_prompt=custom_prompt
)

print(response)
```

---

## ✅ الخلاصة

جميع الأمثلة أعلاه تعمل بشكل صحيح بعد الإصلاح! 🎉

**للمزيد من المعلومات:**
- راجع `chatbot/README_CHATBOT.md` للتوثيق الكامل
- راجع `FINAL_REPORT.md` للتقرير الشامل
- راجع `QUICK_START.md` للبدء السريع

**آخر تحديث:** 2026-05-11
