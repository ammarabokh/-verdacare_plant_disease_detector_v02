import cv2
import numpy as np
from PIL import Image, ImageOps
from tensorflow.keras.applications.efficientnet import preprocess_input


def _fix_orientation(pil_img):
    """Apply EXIF orientation so the image is upright."""
    return ImageOps.exif_transpose(pil_img) or pil_img


def _downscale_if_large(pil_img, max_dim=2000, working_size=800):
    w, h = pil_img.size
    longest = max(w, h)
    if longest > max_dim:
        scale = working_size / longest
        new_w = int(w * scale)
        new_h = int(h * scale)
        return pil_img.resize((new_w, new_h), Image.LANCZOS)
    return pil_img


def _apply_clahe(img_bgr, clip_limit=3.0, tile_size=8):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    l = clahe.apply(l)
    merged = cv2.merge((l, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def _segment_plant(pil_img, green_hue_low=30, green_hue_high=90,
                   saturation_min=40, value_min=40,
                   padding_ratio=0.125, min_contour_ratio=0.05):
    img_rgb = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    lower = np.array([green_hue_low, saturation_min, value_min])
    upper = np.array([green_hue_high, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, pil_img, mask

    largest = max(contours, key=cv2.contourArea)
    img_area = img_bgr.shape[0] * img_bgr.shape[1]
    if cv2.contourArea(largest) / img_area < min_contour_ratio:
        return False, pil_img, mask

    x, y, w, h = cv2.boundingRect(largest)
    pad = int(max(w, h) * padding_ratio)
    H, W = img_bgr.shape[:2]

    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(W, x + w + pad)
    y2 = min(H, y + h + pad)

    cropped_bgr = img_bgr[y1:y2, x1:x2]
    cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
    return True, Image.fromarray(cropped_rgb), mask


def _pad_to_square(pil_img, fill_color=(128, 128, 128)):
    w, h = pil_img.size
    if w == h:
        return pil_img
    max_side = max(w, h)
    result = Image.new('RGB', (max_side, max_side), fill_color)
    paste_x = (max_side - w) // 2
    paste_y = (max_side - h) // 2
    result.paste(pil_img, (paste_x, paste_y))
    return result


def enhanced_preprocess_image(
    image_path,
    target_size=(224, 224),
    max_dim=2000,
    working_size=800,
    use_segmentation=True,
    green_hue_low=30,
    green_hue_high=90,
    saturation_min=40,
    value_min=40,
    padding_ratio=0.125,
    min_contour_ratio=0.05,
    background_color=(128, 128, 128),
    clahe_clip=3.0,
    clahe_tile=8,
    gaussian_ksize=3,
    gaussian_sigma=0.5,
):
    pil_img = Image.open(image_path)
    pil_img = _fix_orientation(pil_img)
    pil_img = pil_img.convert('RGB')

    pil_img = _downscale_if_large(pil_img, max_dim, working_size)

    # Convert to cv2 BGR for CLAHE + blur
    img_rgb = np.array(pil_img)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    img_bgr = _apply_clahe(img_bgr, clahe_clip, clahe_tile)

    img_bgr = cv2.GaussianBlur(img_bgr, (gaussian_ksize, gaussian_ksize), gaussian_sigma)

    # Back to PIL for segmentation
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)

    if use_segmentation:
        success, seg_img, _ = _segment_plant(
            pil_img, green_hue_low, green_hue_high,
            saturation_min, value_min, padding_ratio, min_contour_ratio
        )
        if success:
            pil_img = seg_img

    pil_img = _pad_to_square(pil_img, fill_color=background_color)

    # Resize using INTER_AREA (best for downscaling)
    img_rgb = np.array(pil_img)
    img_resized = cv2.resize(img_rgb, target_size, interpolation=cv2.INTER_AREA)

    img_array = np.expand_dims(img_resized.astype(np.float32), axis=0)
    img_array = preprocess_input(img_array)

    return img_array


def preprocess_image(image_path, target_size=(224, 224)):
    img = Image.open(image_path)
    img = _fix_orientation(img)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img = img.resize(target_size)
    img_array = np.array(img, dtype=np.float32)

    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    return img_array


def check_image_quality(image_path):
    try:
        img = Image.open(image_path)
        img = _fix_orientation(img)
        if img.size[0] < 100 or img.size[1] < 100:
            return False, "too_small"

        img_gray = img.convert('L')
        gray_array = np.array(img_gray, dtype=np.float64)

        mean_brightness = np.mean(gray_array)
        if mean_brightness < 30:
            return False, "too_dark"

        if mean_brightness > 250:
            return False, "too_bright"

        laplacian = (
            4 * gray_array[1:-1, 1:-1]
            - gray_array[:-2, 1:-1]
            - gray_array[2:, 1:-1]
            - gray_array[1:-1, :-2]
            - gray_array[1:-1, 2:]
        )

        laplacian_var = laplacian.var()
        if laplacian_var < 100:
            return False, "blurry"

        return True, "ok"

    except Exception as e:
        return False, f"error"
