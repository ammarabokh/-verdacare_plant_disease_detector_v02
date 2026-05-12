# VerdaCare Plant Disease Detector (v2.0)

تطبيق ويب ذكي لتشخيص أمراض النباتات من صور الأوراق، مع شات بوت زراعي، دعم تعدد اللغات، ولوحة تحكم للمستخدم.

## Overview

- AI diagnosis using TensorFlow/Keras model (EfficientNet-based).
- Disease knowledge base with treatment and prevention guidance.
- Chatbot powered by Hugging Face Inference API.
- User accounts, dashboard, diagnosis history, plant tracking, and settings.
- Multi-language UI: Arabic, English, German.
- Image quality checks (blur/brightness/size) before diagnosis.
- Optional geolocation + diagnosis rating.

## What Is Included in v2.0

- Kaggle model integration with local cache in `models/cache/`.
- Lazy singleton model loader (prevents reloading the model on every request).
- Improved loader compatibility for `kagglehub` APIs.
- Better runtime error handling when model is unavailable.
- Updated SQLAlchemy user loading (`Session.get`).

## Tech Stack

- Backend: Flask, Flask-Login, Flask-Babel, Flask-Session, Flask-WTF
- Database: SQLite via Flask-SQLAlchemy
- ML: TensorFlow, NumPy, OpenCV
- Chatbot: Hugging Face Inference API
- Frontend: Jinja2 templates + JavaScript + Tailwind-style UI

## Quick Start

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
copy .env.example .env
```

4. Edit `.env` (minimum required):

```env
HF_TOKEN=hf_your_token
SECRET_KEY=your_secret_key
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key
KAGGLE_DATASET=username/dataset-name
KAGGLE_MODEL_FILENAME=plant_disease_classifier_efficientnetb0.keras
```

5. Run the app:

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

## Model Loading Behavior

- Preferred path: model exists in `models/cache/` and loads مباشرة.
- If not cached: app tries downloading from Kaggle, then caches locally.
- Loader is lazy + singleton: one model instance per process (not per request).
- If loading fails and `USE_MOCK_IF_MODEL_FAIL=false`, diagnosis endpoint returns `503` with `MODEL_NOT_READY`.

## Main Environment Variables

- `HF_TOKEN`: Hugging Face token (required for chatbot).
- `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_DATASET`, `KAGGLE_MODEL_FILENAME`: model download settings.
- `USE_MOCK_IF_MODEL_FAIL`: `true/false` fallback behavior.
- `SECRET_KEY`: Flask secret key.
- `FLASK_ENV`, `FLASK_DEBUG`: runtime mode.

## Project Structure

```text
verdacare_plant_disease_detector_v02/
├── app.py
├── config.py
├── requirements.txt
├── chatbot/
├── forms/
├── models/
├── routes/
├── static/
├── templates/
├── utils/
├── instance/
└── flask_session/
```

## Troubleshooting

### 1) `MODEL_NOT_READY` or "Model is not loaded"

- Verify Kaggle credentials in `.env`.
- Confirm dataset path is correct (`username/dataset-name`).
- Confirm `KAGGLE_MODEL_FILENAME` exactly matches file name inside dataset.
- Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

- Temporary dev fallback:

```env
USE_MOCK_IF_MODEL_FAIL=true
```

### 2) Kaggle download/API issues

- Make sure account has access to the dataset.
- Check network connectivity.
- Keep `kagglehub` and `kaggle` installed (both are in requirements).

### 3) SQLAlchemy legacy warnings

- Project now uses `db.session.get(...)` in user loader.

## Security Note

إذا تم تسريب أي مفاتيح (`HF_TOKEN`, `KAGGLE_KEY`) يجب عمل rotate فورًا من مزود الخدمة وعدم مشاركتها في المستودع.

## Documentation Map (.md)

- [README_NEW.md](README_NEW.md): دليل شامل محدث للإصدار 2.0.
- [QUICK_START.md](QUICK_START.md): بدء سريع للإصدار القديم.
- [QUICK_START_V2.md](QUICK_START_V2.md): بدء سريع للإصدار 2.0.
- [DEPLOYMENT.md](DEPLOYMENT.md): خيارات النشر (Heroku/Docker/Railway/VPS).
- [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md): الترقية من الإصدارات السابقة.
- [CHANGELOG.md](CHANGELOG.md): سجل التغييرات.
- [CONTRIBUTING.md](CONTRIBUTING.md): إرشادات المساهمة.
- [CHECKLIST.md](CHECKLIST.md): قائمة تحقق للتنفيذ.
- [EXAMPLES.md](EXAMPLES.md): أمثلة استخدام.
- [FINAL_REPORT.md](FINAL_REPORT.md): التقرير النهائي.
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md): ملخص تسليم الإصدار.
- [PHASE1_COMPLETED.md](PHASE1_COMPLETED.md): إنجازات المرحلة الأولى.
- [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md): ملخص المرحلة الأولى.
- [README_PHASE1.md](README_PHASE1.md): وثائق المرحلة الأولى.
- [CHATBOT_FIX_SUMMARY.md](CHATBOT_FIX_SUMMARY.md): ملخص إصلاحات الشات بوت.
- [chatbot/README_CHATBOT.md](chatbot/README_CHATBOT.md): توثيق الشات بوت بالتفصيل.

## License

MIT
