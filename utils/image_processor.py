import numpy as np
from PIL import Image, ImageFilter
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

    if img.mode != 'RGB':
        img = img.convert('RGB')

    img = img.resize(target_size)

    img_array = np.array(img, dtype=np.float32)

    img_array = np.expand_dims(img_array, axis=0)

    return img_array

def check_image_quality(image_path):
    """
    Check if image quality is sufficient for analysis.
    Returns tuple: (is_valid, message)
    """
    try:
        img = Image.open(image_path)

        if img.size[0] < 100 or img.size[1] < 100:
            return False, "Image is too small. Please upload a larger image (minimum 100x100 pixels)."

        img_gray = img.convert('L')
        gray_array = np.array(img_gray, dtype=np.float64)

        mean_brightness = np.mean(gray_array)
        if mean_brightness < 30:
            return False, "Image is too dark. Please take the photo in better lighting conditions."

        if mean_brightness > 250:
            return False, "Image is too bright/overexposed. Please reduce lighting or adjust exposure."

        kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float64)
        padded = np.pad(gray_array, 1, mode='reflect')
        h, w = gray_array.shape
        result = np.zeros((h, w), dtype=np.float64)
        for i in range(h):
            for j in range(w):
                result[i, j] = np.sum(kernel * padded[i:i+3, j:j+3])

        laplacian_var = result.var()
        if laplacian_var < 100:
            return False, "Image is blurry. Please take a clearer, sharper photo."

        return True, "Image quality is good."

    except Exception as e:
        return False, f"Error processing image: {str(e)}"
