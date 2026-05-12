import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WTF_CSRF_ENABLED = True
    HF_TOKEN = os.environ.get('HF_TOKEN')

    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')

    os.makedirs(instance_path, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
     f"sqlite:///{os.path.join(instance_path, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = False
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')

    # Languages
    LANGUAGES = ['ar', 'en', 'de']
    BABEL_DEFAULT_LOCALE = 'ar'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    # Model - Kaggle Integration
    KAGGLE_USERNAME = os.environ.get('KAGGLE_USERNAME')
    KAGGLE_KEY = os.environ.get('KAGGLE_KEY')
    KAGGLE_DATASET = os.environ.get('KAGGLE_DATASET')
    KAGGLE_MODEL_FILENAME = os.environ.get('KAGGLE_MODEL_FILENAME', 'plant_disease_classifier_efficientnetb0.keras')
    
    MODEL_CACHE_DIR = os.path.join(basedir, 'models', 'cache')
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    
    MODEL_PATH = os.path.join(MODEL_CACHE_DIR, KAGGLE_MODEL_FILENAME)
    MODEL_METADATA_PATH = os.path.join(basedir, 'models', 'model_metadata.json')
    KNOWLEDGE_BASE_PATH = os.path.join(basedir, 'chatbot', 'knowledge_base.json')

    # Hugging Face
    HF_MODEL = os.environ.get('HF_MODEL') or "Qwen/Qwen2.5-72B-Instruct"
    HF_MAX_TOKENS = 500
    HF_TEMPERATURE = 0.7

    # Behavior flags
    USE_MOCK_IF_MODEL_FAIL = os.environ.get('USE_MOCK_IF_MODEL_FAIL', 'false').lower() == 'true'
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
