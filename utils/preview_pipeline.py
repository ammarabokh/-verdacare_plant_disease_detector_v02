"""
Preview pipeline steps for a given image.

Usage:
    python utils/preview_pipeline.py <image_path> [--output_dir preview_output]

Shows each preprocessing stage side-by-side and saves results.
"""

import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.image_processor import (
    _downscale_if_large,
    _apply_clahe,
    _segment_plant,
    _pad_to_square,
)
from tensorflow.keras.applications.efficientnet import preprocess_input


def preview_pipeline(image_path, output_dir="preview_output"):
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(image_path))[0]

    print("=" * 60)
    print(f" Image: {image_path}")
    print("=" * 60)

    # ── Original ──
    pil_orig = Image.open(image_path).convert('RGB')
    orig_np = np.array(pil_orig)
    orig_bgr = cv2.cvtColor(orig_np, cv2.COLOR_RGB2BGR)
    print(f"\n[1] Original size: {pil_orig.size}")
    save(orig_bgr, output_dir, f"{base}_01_original.jpg")

    # ── Downscale ──
    pil_down = _downscale_if_large(pil_orig, max_dim=2000, working_size=800)
    down_np = np.array(pil_down)
    down_bgr = cv2.cvtColor(down_np, cv2.COLOR_RGB2BGR)
    print(f"[2] After downscale: {pil_down.size}")
    save(down_bgr, output_dir, f"{base}_02_downscaled.jpg")

    # ── CLAHE ──
    clahe_bgr = _apply_clahe(down_bgr, clip_limit=3.0, tile_size=8)
    print(f"[3] CLAHE applied (clip={3.0}, tile={8}x{8})")
    save(clahe_bgr, output_dir, f"{base}_03_clahe.jpg")

    # ── Gaussian Blur ──
    blurred_bgr = cv2.GaussianBlur(clahe_bgr, (3, 3), 0.5)
    print(f"[4] GaussianBlur applied (ksize=3, sigma=0.5)")
    save(blurred_bgr, output_dir, f"{base}_04_blurred.jpg")

    # ── Segmentation ──
    blurred_rgb = cv2.cvtColor(blurred_bgr, cv2.COLOR_BGR2RGB)
    pil_blurred = Image.fromarray(blurred_rgb)
    success, pil_cropped, mask = _segment_plant(
        pil_blurred, padding_ratio=0.125, green_hue_low=30, green_hue_high=90,
        saturation_min=40, value_min=40, min_contour_ratio=0.05
    )

    # Save mask overlay
    mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    overlay = blurred_bgr.copy()
    overlay[mask > 0] = (0, 255, 0)
    overlay = cv2.addWeighted(blurred_bgr, 0.6, overlay, 0.4, 0)
    # Draw bounding box of largest contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), 2)
    save(overlay, output_dir, f"{base}_05_segmentation.jpg")

    area_ratio = (mask.sum() / 255) / mask.size if mask.sum() > 0 else 0
    print(f"[5] Segmentation: success={success}, green_area={area_ratio:.1%}")

    if success:
        cropped_np = np.array(pil_cropped)
        cropped_bgr = cv2.cvtColor(cropped_np, cv2.COLOR_RGB2BGR)
        print(f"    Cropped size: {pil_cropped.size}")
        save(cropped_bgr, output_dir, f"{base}_06_cropped.jpg")
        current_pil = pil_cropped
    else:
        print("    Segmentation failed, using blurred image")
        current_pil = pil_blurred

    # ── Pad to square (gray) ──
    padded_pil = _pad_to_square(current_pil, fill_color=(128, 128, 128))
    padded_np = np.array(padded_pil)
    padded_bgr = cv2.cvtColor(padded_np, cv2.COLOR_RGB2BGR)
    print(f"[6] Padded to square: {padded_pil.size}")
    save(padded_bgr, output_dir, f"{base}_07_padded.jpg")

    # ── Resize to 224x224 (INTER_AREA) ──
    resized_rgb = cv2.resize(padded_np, (224, 224), interpolation=cv2.INTER_AREA)
    resized_bgr = cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2BGR)
    print(f"[7] Resized to: {resized_rgb.shape[1]}x{resized_rgb.shape[0]} (INTER_AREA)")
    save(resized_bgr, output_dir, f"{base}_08_resized.jpg")

    # ── Final preprocessed (ready for model) ──
    img_array = np.expand_dims(resized_rgb.astype(np.float32), axis=0)
    img_array = preprocess_input(img_array)

    print(f"\n[8] FINAL OUTPUT shape: {img_array.shape}, dtype={img_array.dtype}")
    print(f"    Value range: [{img_array.min():.2f}, {img_array.max():.2f}]")
    print(f"    Mean: [{img_array[0,:,:,0].mean():.2f}, "
          f"{img_array[0,:,:,1].mean():.2f}, "
          f"{img_array[0,:,:,2].mean():.2f}]")

    # Save final as image (inverse preprocess_input for viewing)
    final_display = img_array[0].copy()
    final_display = (final_display - final_display.min())
    final_display = (final_display / final_display.max() * 255).astype(np.uint8)
    save(cv2.cvtColor(final_display, cv2.COLOR_RGB2BGR), output_dir, f"{base}_09_final.jpg")

    print(f"\n All stages saved to: {output_dir}/")
    return img_array


def save(bgr_img, directory, filename):
    path = os.path.join(directory, filename)
    cv2.imwrite(path, bgr_img)
    print(f"    -> saved {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview preprocessing pipeline")
    parser.add_argument("image_path", help="Path to input image")
    parser.add_argument("--output_dir", default="preview_output", help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: image not found: {args.image_path}")
        sys.exit(1)

    preview_pipeline(args.image_path, args.output_dir)
