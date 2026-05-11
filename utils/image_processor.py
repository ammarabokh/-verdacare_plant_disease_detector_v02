import numpy as np
from PIL import Image
import tensorflow as tf

def preprocess_image(image_path, target_size=(224, 224)):
    """
    Preprocess image for model prediction.
    Args:
        image_path: Path to the image file
        target_size: Target size for resizing (default 224x224 for EfficientNetB0)
    Returns:
        Preprocessed image array ready for prediction
    """
    img = Image.open(image_path)

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize
    img = img.resize(target_size)

    # Convert to float32 array.
    # Note: the loaded model already contains an internal Rescaling(1/255) layer,
    # so we must keep pixel range at [0,255] here to avoid double-normalization.
    img_array = np.array(img, dtype=np.float32)

    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)

    return img_array

def check_image_quality(image_path):
    """
    Check if image quality is sufficient for analysis.
    Returns tuple: (is_valid, message)
    """
    try:
        img = Image.open(image_path)

        # Check minimum size
        if img.size[0] < 100 or img.size[1] < 100:
            return False, "Image is too small. Please upload a larger image (minimum 100x100 pixels)."

        # Check if image is too dark
        img_gray = img.convert('L')
        mean_brightness = np.mean(np.array(img_gray))
        if mean_brightness < 30:
            return False, "Image is too dark. Please take the photo in better lighting conditions."

        # Check if image is too bright
        if mean_brightness > 250:
            return False, "Image is too bright/overexposed. Please reduce lighting or adjust exposure."

        return True, "Image quality is good."

    except Exception as e:
        return False, f"Error processing image: {str(e)}"
