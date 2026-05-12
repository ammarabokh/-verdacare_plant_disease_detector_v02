import json
import os
import tensorflow as tf
from config import Config
from threading import Lock
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_model_loader_instance = None
_model_loader_lock = Lock()

class ModelLoader:
    def __init__(self):
        self.model = None
        self.class_names = []
        self.knowledge_base = None
        self.knowledge_base_by_normalized_key = {}
        self.mock_mode = True
        self.load_error = None
        self.load_model()
        self.load_model_metadata()
        self.load_knowledge_base()

    def load_model(self):
        """Load the trained model from cache or download from Kaggle"""
        try:
            if os.path.exists(Config.MODEL_PATH):
                print(f"Loading model from cache: {Config.MODEL_PATH}")
                self.model = tf.keras.models.load_model(Config.MODEL_PATH, compile=False)
                self.mock_mode = False
                self.load_error = None
                print("Model loaded successfully from cache!")
            else:
                print(f"Model not found in cache. Attempting to download from Kaggle...")
                if self._download_model_from_kaggle():
                    self.model = tf.keras.models.load_model(Config.MODEL_PATH, compile=False)
                    self.mock_mode = False
                    self.load_error = None
                    print("Model downloaded and loaded successfully!")
                else:
                    print(f"Warning: Could not download model from Kaggle")
                    self.load_error = "Model download failed"
                    self.mock_mode = Config.USE_MOCK_IF_MODEL_FAIL
                    if self.mock_mode:
                        print("Using mock predictions for testing...")
        except Exception as e:
            self.load_error = str(e)
            print(f"Error loading model: {self.load_error}")
            self.model = None
            self.mock_mode = Config.USE_MOCK_IF_MODEL_FAIL
            if self.mock_mode:
                print("Using mock predictions for testing...")

    def _download_model_from_kaggle(self):
        """Download model from Kaggle using kagglehub"""
        try:
            if not Config.KAGGLE_USERNAME or not Config.KAGGLE_KEY:
                print("Kaggle credentials not configured. Set KAGGLE_USERNAME and KAGGLE_KEY in .env")
                return False
            
            if not Config.KAGGLE_DATASET:
                print("KAGGLE_DATASET not configured in .env")
                return False
            
            os.environ['KAGGLE_USERNAME'] = Config.KAGGLE_USERNAME
            os.environ['KAGGLE_KEY'] = Config.KAGGLE_KEY
            
            print(f"Downloading dataset: {Config.KAGGLE_DATASET}")
            dataset_path = None

            try:
                import kagglehub
                if hasattr(kagglehub, 'dataset_download'):
                    dataset_path = kagglehub.dataset_download(Config.KAGGLE_DATASET)
                elif hasattr(kagglehub, 'model_download'):
                    # kagglehub 0.2.x supports model_download, not dataset_download
                    dataset_path = kagglehub.model_download(Config.KAGGLE_DATASET)
                else:
                    print("kagglehub download API is not available. Falling back to kaggle API...")
            except ImportError:
                print("kagglehub not installed. Falling back to kaggle API...")

            if dataset_path is None:
                dataset_path = self._download_with_kaggle_api()
                if dataset_path is None:
                    return False

            print(f"Dataset downloaded to: {dataset_path}")
            
            source_model_path = os.path.join(dataset_path, Config.KAGGLE_MODEL_FILENAME)

            if not os.path.exists(source_model_path):
                # Search recursively because Kaggle downloads may add nested folders.
                found_path = None
                for root, _, files in os.walk(dataset_path):
                    if Config.KAGGLE_MODEL_FILENAME in files:
                        found_path = os.path.join(root, Config.KAGGLE_MODEL_FILENAME)
                        break
                if found_path:
                    source_model_path = found_path
                else:
                    print(f"Model file not found in downloaded path: {source_model_path}")
                    try:
                        print(f"Top-level files: {os.listdir(dataset_path)}")
                    except Exception:
                        pass
                    return False
            
            import shutil
            shutil.copy2(source_model_path, Config.MODEL_PATH)
            print(f"Model copied to cache: {Config.MODEL_PATH}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading model from Kaggle: {e}")
            return False

    def _download_with_kaggle_api(self):
        """Fallback downloader using kaggle package."""
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            import tempfile
            import zipfile

            dataset = Config.KAGGLE_DATASET
            download_dir = tempfile.mkdtemp(prefix="kaggle_dataset_")

            api = KaggleApi()
            api.authenticate()
            api.dataset_download_files(dataset, path=download_dir, unzip=True, quiet=False)

            zip_name = dataset.split("/")[-1] + ".zip"
            zip_path = os.path.join(download_dir, zip_name)
            if os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(download_dir)

            return download_dir
        except ImportError:
            print("kaggle package not installed. Run: pip install kaggle")
            return None
        except Exception as e:
            print(f"Error downloading with kaggle API: {e}")
            return None

    def load_model_metadata(self):
        """Load class names from model metadata"""
        try:
            if os.path.exists(Config.MODEL_METADATA_PATH):
                with open(Config.MODEL_METADATA_PATH, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                self.class_names = metadata.get('class_names', [])
            else:
                print(f"Warning: Metadata file not found at {Config.MODEL_METADATA_PATH}")
        except Exception as e:
            print(f"Error loading model metadata: {e}")
            self.class_names = []

    def load_knowledge_base(self):
        """Load disease knowledge base"""
        try:
            with open(Config.KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.knowledge_base = data['diseases']
                self.knowledge_base_by_normalized_key = {
                    self._normalize_label(k): k for k in self.knowledge_base.keys()
                }
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            self.knowledge_base = {}
            self.knowledge_base_by_normalized_key = {}

    def predict(self, preprocessed_image):
        """
        Make prediction on preprocessed image.
        Returns: (predicted_class, confidence, disease_info)
        """
        if self.model is None:
            if not self.mock_mode:
                raise RuntimeError(
                    "Model is not loaded. This is usually a Keras/TensorFlow version mismatch with the .keras file. "
                    f"Load error: {self.load_error}"
                )
            # Mock prediction for testing
            import random
            classes = list(self.knowledge_base.keys()) if self.knowledge_base else [
                'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___healthy'
            ]
            predicted_class = random.choice(classes)
            confidence = random.uniform(0.75, 0.98)
            return predicted_class, confidence, self.get_disease_info(predicted_class)

        # Real prediction
        predictions = self.model.predict(preprocessed_image)
        predicted_idx = int(tf.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_idx])

        # Get class name from model metadata or use index
        # This assumes you have a metadata file with class mapping
        class_name = self.get_class_name(predicted_idx)

        return class_name, confidence, self.get_disease_info(class_name)

    def get_class_name(self, idx):
        """Get class name from index"""
        if idx < len(self.class_names):
            return self.class_names[idx]

        # Fallback: use knowledge base keys
        classes = list(self.knowledge_base.keys())
        if idx < len(classes):
            return classes[idx]

        return f"Class_{idx}"

    def get_disease_info(self, class_name):
        """Get disease information from knowledge base"""
        if class_name in self.knowledge_base:
            return self.knowledge_base[class_name]

        normalized = self._normalize_label(class_name)
        matched_key = self.knowledge_base_by_normalized_key.get(normalized)
        if matched_key:
            return self.knowledge_base.get(matched_key)

        return None

    def _normalize_label(self, label):
        """Normalize class labels to improve matching across naming styles."""
        if not label:
            return ""
        normalized = label.strip().lower().replace("___", "_")
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        return normalized

def get_model_loader():
    """Thread-safe singleton accessor with lazy initialization."""
    global _model_loader_instance
    if _model_loader_instance is None:
        with _model_loader_lock:
            if _model_loader_instance is None:
                _model_loader_instance = ModelLoader()
    return _model_loader_instance
