# backend/ai_engine/cloth_cleaner.py
import io
from PIL import Image
from rembg import remove
import numpy as np
import cv2

def clean_cloth(cloth_img: Image.Image, cloth_type: str = "shirt") -> Image.Image:
    """
    Removes background and filters out skin-like regions from cloth image.
    
    Args:
        cloth_img: PIL Image of the clothing
        cloth_type: Type of clothing (shirt, dress, etc.)
        
    Returns:
        PIL Image with clean clothing on transparent background
    """
    print(f"🧹 Cleaning {cloth_type} image...")
    
    # Step 1: Ensure RGBA mode
    if cloth_img.mode != "RGBA":
        print(f"Converting image from {cloth_img.mode} to RGBA")
        cloth_img = cloth_img.convert("RGBA")
    
    # Step 2: Remove background
    print("Removing background...")
    try:
        no_bg = remove(cloth_img)  # Still might have face/hands
        print("✅ Background removal successful")
    except Exception as e:
        print(f"❌ Background removal failed: {e}")
        raise

    try:
        print("Converting to OpenCV format for skin removal...")
        # Step 3: Convert to OpenCV for skin removal
        np_img = np.array(no_bg)
        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # Skin color range (tune if needed)
        lower_skin = np.array([0, 40, 0], dtype=np.uint8)
        upper_skin = np.array([25, 255, 255], dtype=np.uint8)

        print("Removing skin-colored regions...")
        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        # Step 4: Remove skin pixels by making them transparent
        np_img[mask > 0] = (0, 0, 0, 0)

        # Step 5: Back to PIL
        cleaned = Image.fromarray(np_img, "RGBA")
        print("✅ Skin removal and cleaning completed")
        return cleaned
        
    except Exception as e:
        print(f"❌ Skin removal processing failed: {e}")
        print("⚠️ Returning original background-removed image as fallback")
        return no_bg
