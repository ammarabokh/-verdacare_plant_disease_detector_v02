#!/usr/bin/env python3
"""
🧪 اختبار الاتصال بـ Hugging Face
شغّل هذا الملف للتأكد من أن كل شيء يعمل
"""

import os
import sys
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def test_token():
    """اختبر وجود HF_TOKEN"""
    print("=" * 60)
    print("✅ اختبار 1: التحقق من HF_TOKEN")
    print("=" * 60)
    
    token = os.environ.get("HF_TOKEN")
    
    if not token:
        print("❌ خطأ: HF_TOKEN غير موجود في .env")
        print("   الحل: أضف السطر التالي في ملف .env:")
        print("   HF_TOKEN=hf_your_token_here")
        return False
    
    if not token.startswith("hf_"):
        print("⚠️  تحذير: التوكن قد لا يكون صحيح")
        print("   يجب أن يبدأ بـ 'hf_'")
        return False
    
    print(f"✅ تم العثور على التوكن: {token[:20]}...")
    return True


def test_imports():
    """اختبر استيراد المكتبات"""
    print("\n" + "=" * 60)
    print("✅ اختبار 2: التحقق من المكتبات")
    print("=" * 60)
    
    try:
        from huggingface_hub import InferenceClient
        print("✅ تم تثبيت huggingface_hub")
    except ImportError:
        print("❌ خطأ: huggingface_hub غير مثبت")
        print("   الحل: اكتب في Terminal:")
        print("   pip install huggingface-hub")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ تم تثبيت python-dotenv")
    except ImportError:
        print("❌ خطأ: python-dotenv غير مثبت")
        print("   الحل: اكتب في Terminal:")
        print("   pip install python-dotenv")
        return False
    
    return True


def test_hf_client():
    """اختبر إنشء عميل Hugging Face"""
    print("\n" + "=" * 60)
    print("✅ اختبار 3: إنشء عميل Hugging Face")
    print("=" * 60)
    
    try:
        # حاول استيراد وإنشاء العميل
        from huggingface_hub import InferenceClient
        
        token = os.environ.get("HF_TOKEN")
        if not token:
            print("❌ خطأ: لا يوجد token")
            return False
        
        client = InferenceClient(api_key=token)
        print("✅ تم إنشاء عميل Hugging Face بنجاح")
        return True
    
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return False


def test_model_response():
    """اختبر الحصول على رد من النموذج"""
    print("\n" + "=" * 60)
    print("✅ اختبار 4: اختبار الرد من النموذج")
    print("=" * 60)
    print("⏳ جاري الاختبار... قد يستغرق بضع ثوانٍ...")
    
    try:
        from huggingface_hub import InferenceClient
        
        token = os.environ.get("HF_TOKEN")
        client = InferenceClient(api_key=token)
        
        # اختبر بسؤال بسيط
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is a tomato plant?"}
        ]
        
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            stream=False,
        )
        
        reply = response.choices[0].message.content
        print(f"✅ تم الحصول على رد من النموذج!")
        print(f"   الرد: {reply[:100]}...")
        return True
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ خطأ: {error_msg}")
        
        if "404" in error_msg or "Not Found" in error_msg:
            print("   السبب: النموذج غير متاح")
            print("   الحل: جرب هذا الأمر لقائمة النماذج المتاحة")
        elif "Unauthorized" in error_msg or "401" in error_msg:
            print("   السبب: التوكن غير صحيح")
            print("   الحل: تحقق من التوكن في .env")
        elif "Rate limit" in error_msg:
            print("   السبب: تم تجاوز حد الطلبات")
            print("   الحل: انتظر بضع دقائق وحاول مرة أخرى")
        
        return False


def test_chatbot_logic():
    """اختبر chatbot_logic.py"""
    print("\n" + "=" * 60)
    print("✅ اختبار 5: اختبار chatbot_logic")
    print("=" * 60)
    
    try:
        # تأكد من أن الملفات موجودة
        if not os.path.exists("chatbot/chatbot_logic.py"):
            print("❌ خطأ: chatbot/chatbot_logic.py غير موجود")
            return False
        
        if not os.path.exists("chatbot/huggingface_client.py"):
            print("❌ خطأ: chatbot/huggingface_client.py غير موجود")
            return False
        
        print("✅ تم العثور على ملفات chatbot")
        
        # حاول استيراد chatbot_logic
        from chatbot.chatbot_logic import chatbot
        print("✅ تم استيراد chatbot_logic بنجاح")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return False


def print_summary(results):
    """طباعة ملخص الاختبارات"""
    print("\n" + "=" * 60)
    print("📊 ملخص الاختبارات")
    print("=" * 60)
    
    tests = [
        ("التوكن", results[0]),
        ("المكتبات", results[1]),
        ("عميل HF", results[2]),
        ("رد النموذج", results[3]),
        ("Chatbot Logic", results[4]),
    ]
    
    passed = sum(results)
    total = len(results)
    
    for name, passed_test in tests:
        status = "✅ نجح" if passed_test else "❌ فشل"
        print(f"{name:20} {status}")
    
    print("=" * 60)
    print(f"النتيجة: {passed}/{total} اختبارات نجحت")
    
    if passed == total:
        print("\n🎉 ممتاز! كل شيء يعمل بشكل صحيح!")
        print("يمكنك الآن تشغيل التطبيق: python app.py")
        return True
    else:
        print("\n⚠️  بعض الاختبارات فشلت")
        print("راجع الأخطاء أعلاه وحاول إصلاحها")
        return False


def main():
    """تشغيل جميع الاختبارات"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║ 🧪 اختبار الاتصال بـ Hugging Face" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    results.append(test_token())
    results.append(test_imports())
    results.append(test_hf_client())
    results.append(test_model_response())
    results.append(test_chatbot_logic())
    
    success = print_summary(results)
    
    print("\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())