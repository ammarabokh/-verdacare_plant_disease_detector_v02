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
    KAGGLE_NOTEBOOK = os.environ.get('KAGGLE_NOTEBOOK')
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

    # One-time admin bootstrap (safe alternative to hardcoded admin credentials)
    ADMIN_BOOTSTRAP_ENABLED = os.environ.get('ADMIN_BOOTSTRAP_ENABLED', 'false').lower() == 'true'
    ADMIN_BOOTSTRAP_USERNAME = os.environ.get('ADMIN_BOOTSTRAP_USERNAME', '').strip()
    ADMIN_BOOTSTRAP_EMAIL = os.environ.get('ADMIN_BOOTSTRAP_EMAIL', '').strip()
    ADMIN_BOOTSTRAP_PASSWORD = os.environ.get('ADMIN_BOOTSTRAP_PASSWORD', '')
    ADMIN_BOOTSTRAP_FULL_NAME = os.environ.get('ADMIN_BOOTSTRAP_FULL_NAME', '').strip()
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Image preprocessing settings
    MAX_IMAGE_DIMENSION = 2000          # downscale if longest side exceeds this
    WORKING_IMAGE_SIZE = 800            # target size after downscale
    USE_BACKGROUND_SEGMENTATION = True  # enable leaf isolation
    GREEN_HUE_LOW = 30                  # HSV hue lower bound for green
    GREEN_HUE_HIGH = 90                 # HSV hue upper bound for green
    SATURATION_THRESHOLD = 40           # minimum saturation for green mask
    VALUE_THRESHOLD = 40                # minimum value (brightness) for green mask
    PADDING_RATIO = 0.125               # padding around leaf bounding box (~80% coverage)
    MIN_CONTOUR_AREA_RATIO = 0.05       # minimum leaf area ratio (5%)
    BACKGROUND_COLOR = (128, 128, 128)  # background fill color (gray)
    CLAHE_CLIP_LIMIT = 3.0              # CLAHE contrast clip limit
    CLAHE_TILE_SIZE = 8                 # CLAHE tile grid size (8x8)
    GAUSSIAN_BLUR_KSIZE = 3             # Gaussian kernel size (must be odd)
    GAUSSIAN_BLUR_SIGMA = 0.5           # Gaussian sigma value
