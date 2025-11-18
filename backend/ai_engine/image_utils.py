import os
from PIL import Image

def validate_and_preprocess_image(img: Image.Image, min_size: int = 256, max_size: int = 1024) -> Image.Image:
    """
    Validates and preprocesses an image for the try-on pipeline.
    Ensures proper size and format.
    """
    # Check minimum size
    w, h = img.size
    if w < min_size or h < min_size:
        raise ValueError(f"Image too small. Minimum dimension required: {min_size}px")
        
    # Resize if too large while maintaining aspect ratio
    if w > max_size or h > max_size:
        aspect = w / h
        if w > h:
            new_w = max_size
            new_h = int(max_size / aspect)
        else:
            new_h = max_size
            new_w = int(max_size * aspect)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
    # Ensure proper color mode and depth
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        
    return img

def cleanup_temp_files(file_list: list):
    """
    Safely removes temporary files created during processing.
    """
    for file_path in file_list:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️ Warning: Could not remove temp file {file_path}: {e}")