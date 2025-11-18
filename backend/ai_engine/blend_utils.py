import cv2
import numpy as np
from PIL import Image

def apply_advanced_blending(base_img: np.ndarray, overlay_img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Apply advanced blending between base image and overlay with smooth transitions.
    
    Args:
        base_img: Background image (user photo)
        overlay_img: Foreground image (warped clothing)
        mask: Alpha mask for blending
    """
    # Ensure images are RGBA
    if base_img.shape[2] == 3:
        base_img = cv2.cvtColor(base_img, cv2.COLOR_RGB2RGBA)
    if overlay_img.shape[2] == 3:
        overlay_img = cv2.cvtColor(overlay_img, cv2.COLOR_RGB2RGBA)
        
    # Create feathered mask
    kernel_size = max(3, min(overlay_img.shape[0] // 50, 15))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # Create gradual transition
    mask_dilated = cv2.dilate(mask, kernel, iterations=2)
    mask_blurred = cv2.GaussianBlur(mask_dilated, (kernel_size, kernel_size), 0)
    
    # Normalize mask to range [0, 1]
    alpha = mask_blurred.astype(float) / 255
    
    # Add dimension for broadcasting
    alpha = np.expand_dims(alpha, axis=2)
    
    # Blend images using the mask
    blended = (base_img.astype(float) * (1 - alpha) + 
              overlay_img.astype(float) * alpha)
    
    # Ensure valid range
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    return blended