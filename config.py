import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    HF_TOKEN = os.environ.get('HF_TOKEN')

    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')

    os.makedirs(instance_path, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
     f"sqlite:///{os.path.join(instance_path, 'app.db')}"
    
    # Flask-Session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = False
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')

    # Languages
    LANGUAGES = ['ar', 'en']
    BABEL_DEFAULT_LOCALE = 'ar'
    BABEL_DEFAULT_TIMEZONE = 'UTC'

    # Model
    MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'plant_disease_classifier_efficientnetb0.keras')
    MODEL_METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'model_metadata.json')
    KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatbot', 'knowledge_base.json')

    # Hugging Face
    HF_MODEL = os.environ.get('HF_MODEL') or "Qwen/Qwen2.5-72B-Instruct"
    HF_MAX_TOKENS = 500
    HF_TEMPERATURE = 0.7

    # Behavior flags
    USE_MOCK_IF_MODEL_FAIL = os.environ.get('USE_MOCK_IF_MODEL_FAIL', 'false').lower() == 'true'
