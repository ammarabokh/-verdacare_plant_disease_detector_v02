import json
import os
import tensorflow as tf
from config import Config

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
        """Load the trained model"""
        try:
            if os.path.exists(Config.MODEL_PATH):
                self.model = tf.keras.models.load_model(Config.MODEL_PATH, compile=False)
                self.mock_mode = False
                self.load_error = None
                print("Model loaded successfully!")
            else:
                print(f"Warning: Model file not found at {Config.MODEL_PATH}")
                self.load_error = f"Model file not found at {Config.MODEL_PATH}"
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

# Singleton instance
model_loader = ModelLoader()
