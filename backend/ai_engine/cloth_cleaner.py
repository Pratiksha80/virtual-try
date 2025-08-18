# backend/ai_engine/cloth_cleaner.py
import io
from PIL import Image
from rembg import remove
import numpy as np
import cv2

def clean_cloth(cloth_path: str) -> Image.Image:
    """Removes background and filters out skin-like regions from cloth image."""
    # Step 1: Remove background
    cloth_img = Image.open(cloth_path).convert("RGBA")
    no_bg = remove(cloth_img)  # Still might have face/hands

    # Step 2: Convert to OpenCV for skin removal
    np_img = np.array(no_bg)
    bgr = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Skin color range (tune if needed)
    lower_skin = np.array([0, 40, 0], dtype=np.uint8)
    upper_skin = np.array([25, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Step 3: Remove skin pixels by making them transparent
    np_img[mask > 0] = (0, 0, 0, 0)

    # Step 4: Back to PIL
    cleaned = Image.fromarray(np_img, "RGBA")
    return cleaned
