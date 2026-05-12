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
        self.download_error = None
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
                    self.load_error = f"Model download failed: {self.download_error or 'unknown download error'}"
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
        """Download only the configured .keras model file from Kaggle."""
        try:
            self.download_error = None
            if not Config.KAGGLE_USERNAME or not Config.KAGGLE_KEY:
                msg = "Kaggle credentials not configured. Set KAGGLE_USERNAME and KAGGLE_KEY."
                print(msg)
                self.download_error = msg
                return False
            
            if not Config.KAGGLE_DATASET:
                msg = "KAGGLE_DATASET is not configured."
                print(msg)
                self.download_error = msg
                return False

            if not Config.KAGGLE_MODEL_FILENAME.lower().endswith(".keras"):
                msg = f"KAGGLE_MODEL_FILENAME must be a .keras file. Got: {Config.KAGGLE_MODEL_FILENAME}"
                print(msg)
                self.download_error = msg
                return False
            
            os.environ['KAGGLE_USERNAME'] = Config.KAGGLE_USERNAME
            os.environ['KAGGLE_KEY'] = Config.KAGGLE_KEY

            # Strategy 1: kaggle API single-file download (best: downloads only .keras)
            if self._download_keras_file_with_kaggle_api():
                return True

            # Strategy 2: kagglehub fallback for environments where kaggle API fails
            if self._download_with_kagglehub_fallback():
                return True

            return False

        except Exception as e:
            print(f"Error downloading model from Kaggle: {e}")
            self.download_error = str(e)
            return False

    def _download_keras_file_with_kaggle_api(self):
        """Download only one file from a Kaggle dataset: Config.KAGGLE_MODEL_FILENAME."""
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            import tempfile
            import zipfile
            import shutil

            dataset = Config.KAGGLE_DATASET
            filename = Config.KAGGLE_MODEL_FILENAME
            download_dir = tempfile.mkdtemp(prefix="kaggle_model_file_")

            api = KaggleApi()
            api.authenticate()

            print(f"Downloading file from Kaggle dataset: {dataset}/{filename}")
            api.dataset_download_file(
                dataset=dataset,
                file_name=filename,
                path=download_dir,
                force=False,
                quiet=False
            )

            # Kaggle API downloads as <filename>.zip
            zip_path = os.path.join(download_dir, f"{filename}.zip")
            if not os.path.exists(zip_path):
                msg = f"Downloaded zip not found: {zip_path}"
                print(msg)
                self.download_error = msg
                return False

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(download_dir)

            source_model_path = os.path.join(download_dir, filename)
            if not os.path.exists(source_model_path):
                msg = f"Extracted model file not found: {source_model_path}"
                print(msg)
                self.download_error = msg
                return False

            shutil.copy2(source_model_path, Config.MODEL_PATH)
            print(f"Model file downloaded and cached at: {Config.MODEL_PATH}")
            return True
        except ImportError:
            msg = "kaggle package not installed. Run: pip install kaggle"
            print(msg)
            self.download_error = msg
            return False
        except Exception as e:
            msg = f"Error downloading model file with kaggle API: {e}"
            print(msg)
            self.download_error = msg
            return False

    def _download_with_kagglehub_fallback(self):
        """Fallback: use kagglehub then locate/copy only the target .keras file."""
        try:
            import kagglehub
            import shutil

            dataset_path = None
            if hasattr(kagglehub, "dataset_download"):
                dataset_path = kagglehub.dataset_download(Config.KAGGLE_DATASET)
            elif hasattr(kagglehub, "model_download"):
                dataset_path = kagglehub.model_download(Config.KAGGLE_DATASET)
            else:
                self.download_error = "kagglehub has no supported download method"
                return False

            if not dataset_path or not os.path.exists(dataset_path):
                self.download_error = f"kagglehub returned invalid path: {dataset_path}"
                return False

            target = Config.KAGGLE_MODEL_FILENAME
            source_model_path = os.path.join(dataset_path, target)
            if not os.path.exists(source_model_path):
                found_path = None
                for root, _, files in os.walk(dataset_path):
                    if target in files:
                        found_path = os.path.join(root, target)
                        break
                if found_path:
                    source_model_path = found_path
                else:
                    self.download_error = f"Model file '{target}' not found in KaggleHub download"
                    return False

            shutil.copy2(source_model_path, Config.MODEL_PATH)
            print(f"Model file copied from kagglehub to cache: {Config.MODEL_PATH}")
            return True
        except ImportError:
            # keep previous detailed error from kaggle API path if available
            if not self.download_error:
                self.download_error = "kagglehub package not installed"
            return False
        except Exception as e:
            self.download_error = f"kagglehub fallback failed: {e}"
            return False

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
