# 🌿 Plant Disease Detector v1.0

تطبيق ويب لاكتشاف أمراض النباتات باستخدام الذكاء الاصطناعي | AI-Powered Plant Disease Detection Web App

## ✨ الميزات | Features

- 🤖 **تشخيص ذكي** - نموذج EfficientNetB0 للتعرف على 38 مرض نباتي
- 📊 **تقارير مفصلة** - وصف المرض، الأعراض، العلاج، الوقاية، والمنتجات الموصى بها
- 💬 **شات بوت ذكي** - مساعد زراعي يعمل بـ Hugging Face LLM مع ذاكرة محادثة
- 🌙 **وضع داكن** - دعم الوضع الفاتح والداكن
- 🌍 **تعدد اللغات** - العربية والإنجليزية
- 📱 **تصميم متجاوب** - يعمل على جميع الأجهزة

## 🚀 التثبيت | Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd plant_disease_detector_v01
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your Hugging Face token:
```
HF_TOKEN=hf_your_token_here
SECRET_KEY=your-secret-key-here
```

### 5. Add your model
Place your trained model file in:
```
models/efficientnetb0.h5
```

And metadata file:
```
models/metadata.json
```

Example `metadata.json`:
```json
{
  "class_names": [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Tomato___Early_blight",
    ...
  ]
}
```

### 6. Run the application
```bash
python app.py
```

Visit: http://localhost:5000

## 📁 هيكل المشروع | Project Structure

```
plant_disease_detector_v01/
├── app.py                          # Flask application
├── config.py                       # Configuration
├── requirements.txt                # Dependencies
├── .env                            # Environment variables
├── .env.example                    # Example environment file
├── .gitignore                      # Git ignore rules
├── models/
│   ├── efficientnetb0.h5          # Trained model (add yours)
│   └── metadata.json              # Class names mapping
├── static/
│   ├── css/                        # Stylesheets
│   ├── js/
│   │   └── main.js                 # Frontend JavaScript
│   └── uploads/                    # Uploaded images
├── templates/
│   ├── base.html                   # Base template
│   ├── index.html                  # Home page
│   ├── result.html                 # Diagnosis result
│   └── includes/                  # Template components
├── utils/
│   ├── image_processor.py          # Image preprocessing
│   ├── model_loader.py            # Model loading & prediction
│   └── report_generator.py        # HTML report generation
├── chatbot/
│   ├── huggingface_client.py      # Hugging Face API client
│   ├── chat_memory.py             # Conversation memory
│   ├── chatbot_logic.py           # Chatbot logic
│   └── knowledge_base.json        # Disease knowledge base
└── instance/
    └── app.db                      # SQLite database
```

## 🔑 الحصول على Hugging Face Token

1. Visit [huggingface.co](https://huggingface.co)
2. Create a free account
3. Go to **Settings → Access Tokens**
4. Click **New Token**
5. Select **Read** role
6. Copy the token and paste in `.env`

## 📝 ملاحظات | Notes

- The application uses a **mock prediction** if no model file is found (for testing)
- Conversation memory is stored **in-memory** and resets when the server restarts
- For production, consider using Redis for session and memory storage
- The knowledge base contains information for **38 plant diseases**

## 🔧 Troubleshooting

### Hugging Face API errors
- Check your token is valid
- Ensure you have internet connection
- The model used is `openai/gpt-oss-120b:groq` via Hugging Face Inference API

### Model not loading
- Verify `efficientnetb0.h5` exists in `models/`
- Check TensorFlow version compatibility
- Use the mock mode for testing without a model

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Developed with ❤️ for farmers worldwide**
