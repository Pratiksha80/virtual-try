import io
import base64
import os
import requests
import sys
import time
import ssl
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import urllib3

from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from rembg import remove, new_session
import cv2
import numpy as np
from scipy import ndimage
from sklearn.cluster import KMeans

from ai_engine import warp_mesh, fit_polygons, person_pose, viton_hd

# --- Setup & Configuration ---

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure a directory for saving intermediate and debug images
DEBUG_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "debug"))
print(f"Debug directory: {DEBUG_DIR}")
os.makedirs(DEBUG_DIR, exist_ok=True)

# Initialize the background removal session for clothing
try:
    cloth_session = new_session("u2net_cloth_seg")
except Exception as e:
    print(f"Warning: Could not initialize cloth segmentation: {e}")
    cloth_session = None

# Initialize VITON-HD model
viton_model = viton_hd.get_viton_model()


def process_tryon(user_img_source: str, cloth_img_source: str, cloth_type: str = "shirt"):
    """
    Process virtual try-on request.
    Args:
        user_img_source: URL or base64 of user image
        cloth_img_source: URL or base64 of clothing image
        cloth_type: Type of clothing ("shirt", "dress", etc.)
    Returns:
        dict: Result with processed image or error
    """
    try:
        print(f"\n🔄 Processing try-on request for {cloth_type}")
        print(f"📸 User image source: {user_img_source[:50]}...")
        print(f"👕 Cloth image source: {cloth_img_source[:50]}...")
        
        # Get image paths
        print("🔍 Converting image sources to paths...")
        user_path = get_image_path(user_img_source, "user")
        cloth_path = get_image_path(cloth_img_source, "cloth")
        
        print(f"📁 User image path: {user_path}")
        print(f"📁 Cloth image path: {cloth_path}")
        
        # Verify paths exist
        if not os.path.exists(user_path):
            print(f"❌ User image not found at: {user_path}")
            raise FileNotFoundError(f"User image not found at: {user_path}")
            
        if not os.path.exists(cloth_path):
            print(f"❌ Cloth image not found at: {cloth_path}")
            raise FileNotFoundError(f"Cloth image not found at: {cloth_path}")
        
        # Process images
        print("🖼 Opening images...")
        try:
            cloth_img = Image.open(cloth_path)
            print(f"✅ Cloth image opened successfully: {cloth_img.size} {cloth_img.mode}")
        except Exception as e:
            print(f"❌ Failed to open cloth image: {e}")
            raise
            
        try:
            user_img = Image.open(user_path)
            print(f"✅ User image opened successfully: {user_img.size} {user_img.mode}")
        except Exception as e:
            print(f"❌ Failed to open user image: {e}")
            raise

        # Clean cloth image
        print("🧹 Cleaning cloth image...")
        try:
            cleaned_cloth = clean_cloth(cloth_img, cloth_type)
            print(f"✅ Cloth image cleaned successfully: {cleaned_cloth.size} {cleaned_cloth.mode}")
            save_debug_image(cleaned_cloth, "cleaned_cloth.png")
            print("✅ Debug image saved: cleaned_cloth.png")
        except Exception as e:
            print(f"❌ Failed to clean cloth image: {e}")
            raise
        
        try:
            print("🔄 Attempting VITON-HD processing...")
            # Try VITON-HD first
            result_img = viton_model.process(user_img, cleaned_cloth)
            save_debug_image(result_img, "viton_result.png")
            print("✅ Successfully used VITON-HD")
            
        except Exception as viton_error:
            print(f"⚠ VITON-HD failed, falling back to geometric warping:")
            print(f"Error details: {str(viton_error)}")
            import traceback
            traceback.print_exc()
            
            print("🏃 Starting geometric warping fallback...")
            
            try:
                # Get user pose and measurements
                print("👤 Detecting pose keypoints...")
                pose_info = person_pose.infer_keypoints(user_path)
                print("✅ Pose detection successful")
                print(f"Found {len(pose_info['kps'])} keypoints")
                
                measurements = get_body_measurements(pose_info["kps"], pose_info["index_map"])
                print("✅ Body measurements calculated")
                
                # Create warping mesh
                print("🔲 Creating warping mesh...")
                dst_poly = create_realistic_polygon(measurements, cloth_type, np.array(user_img))
                print("✅ Warping mesh created")
                
                # Warp cloth onto user
                print("👕 Warping cloth onto user...")
                result_img = warp_mesh.warp_rgba_mesh(
                    np.array(cleaned_cloth),
                    src_pts=fit_polygons.get_source_points(cleaned_cloth),
                    dst_pts=dst_poly,
                    out_wh=user_img.size
                )
                result_img = Image.fromarray(result_img)
                print("✅ Cloth warping completed")
                
            except Exception as fallback_error:
                print(f"❌ Geometric warping fallback also failed:")
                print(f"Error details: {str(fallback_error)}")
                import traceback
                traceback.print_exc()
                raise
        
        # Save result and convert to base64
        try:
            print("💾 Saving result image...")
            result_path = os.path.join(DEBUG_DIR, "result.png")
            result_img.save(result_path, "PNG")
            print(f"✅ Result saved to: {result_path}")
            
            print("🔄 Converting result to base64...")
            # Convert to base64
            buffered = io.BytesIO()
            result_img.save(buffered, format="PNG")
            img_data = base64.b64encode(buffered.getvalue()).decode()
            output_image_base64 = f"data:image/png;base64,{img_data}"
            print("✅ Base64 conversion successful")

            # Return a consistent key expected by the routes (output_image_base64)
            return {
                "output_image_base64": output_image_base64
            }
            
        except Exception as save_error:
            print(f"❌ Error saving/converting result: {save_error}")
            raise RuntimeError(f"Failed to process output image: {save_error}")
        
    except Exception as e:
        print(f"❌ Error in process_tryon: {e}")
        raise RuntimeError(f"Try-on process failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# --- Image Fetching & Network Utilities ---

def create_robust_session():
    """Create a requests session with robust settings for retries and headers."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    })
    return session

def capture_image_from_url(url, output_path, max_retries=3):
    """Capture an image from a URL with robust error handling, SSL flexibility, and retries."""
    print(f"📸 Capturing image from: {url}")
    session = create_robust_session()
    session.headers.update({
        'Accept': 'image/webp,image/apng,image/svg+xml,image/,/*;q=0.8',
    })

    for attempt in range(max_retries):
        try:
            print(f"📥 Download attempt {attempt + 1}/{max_retries}")
            response = None
            try:
                # First, try with SSL verification enabled
                response = session.get(url, timeout=30, stream=True, allow_redirects=True)
            except (ssl.SSLError, requests.exceptions.SSLError):
                print("⚠ SSL issue, retrying without verification...")
                response = session.get(url, timeout=30, stream=True, allow_redirects=True, verify=False)

            response.raise_for_status()

            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"⚠ Warning: Content-Type is '{content_type}', not an image. Proceeding anyway.")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ Image saved successfully: {output_path} ({file_size_mb:.2f}MB)")
                return True
            else:
                raise Exception("Downloaded file is empty or does not exist.")

        except requests.exceptions.RequestException as e:
            print(f"📡 Network error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            continue
        except Exception as e:
            print(f"❌ Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue

    print(f"❌ Failed to capture image after {max_retries} attempts.")
    return False

def validate_image_file(file_path):
    """Validate that the downloaded file is a valid image using PIL."""
    try:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False, "File is empty or does not exist"
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image
        with Image.open(file_path) as img:
            return True, f"Format: {img.format}, Size: {img.size}"
    except Exception as e:
        return False, f"Invalid image file: {e}"

def get_image_path(source: str, prefix: str) -> str:
    """
    Checks if the source is a URL or a local file. If it's a URL, downloads it
    and returns the local path. If a local file, verifies and returns the path.
    """
    is_url = source.startswith("http://") or source.startswith("https://")

    if is_url:
        print(f"Source is a URL: {source}")
        file_extension = os.path.splitext(source.split('?')[0])[-1] or '.png'
        output_path = os.path.join(DEBUG_DIR, f"{prefix}_{int(time.time())}{file_extension}")

        if capture_image_from_url(source, output_path):
            is_valid, info = validate_image_file(output_path)
            if is_valid:
                print(f"✅ URL image downloaded and validated: {output_path}")
                return output_path
            else:
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise ValueError(f"Downloaded file from {source} is not a valid image: {info}")
        else:
            raise ConnectionError(f"Failed to download image from URL: {source}")
    else:
        print(f"Source is a local path: {source}")
        if not os.path.exists(source):
            raise FileNotFoundError(f"Local image file not found: {source}")
        return source

# --- Try-On Core Logic ---

def save_debug_image(img_pil, name):
    """Saves an image to the debug directory."""
    try:
        path = os.path.join(DEBUG_DIR, name)
        img_pil.save(path)
        print(f"🖼  Saved debug image: {path}")
    except Exception as e:
        print(f"⚠ Could not save debug image {name}: {e}")

def create_debug_visualization(user_img, cloth_img, kps, idx_map, measurements, dst_poly, cloth_type):
    """Create a comprehensive debug visualization showing all processing steps."""
    try:
        # Create a large debug image with multiple panels
        debug_img = np.zeros((user_img.height * 2, user_img.width * 2, 3), dtype=np.uint8)
        
        # Panel 1: Original user image with keypoints
        user_with_kps = np.array(user_img.convert("RGB"))
        for name, idx in idx_map.items():
            if idx < len(kps):
                x, y = int(kps[idx][0]), int(kps[idx][1])
                cv2.circle(user_with_kps, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(user_with_kps, name, (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
        debug_img[:user_img.height, :user_img.width] = user_with_kps
        
        # Panel 2: Cloth image
        cloth_resized = cloth_img.resize((user_img.width, user_img.height), Image.LANCZOS)
        debug_img[:user_img.height, user_img.width:] = np.array(cloth_resized.convert("RGB"))
        
        # Panel 3: User image with polygon overlay
        user_with_poly = np.array(user_img.convert("RGB"))
        if dst_poly is not None:
            cv2.polylines(user_with_poly, [dst_poly.astype(int)], isClosed=True, color=(255, 0, 0), thickness=3)
            for i, (x, y) in enumerate(dst_poly.astype(int)):
                cv2.circle(user_with_poly, (int(x), int(y)), 8, (0, 0, 255), -1)
                cv2.putText(user_with_poly, str(i), (int(x)+10, int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        debug_img[user_img.height:, :user_img.width] = user_with_poly
        
        # Panel 4: Measurements and info
        info_img = np.ones((user_img.height, user_img.width, 3), dtype=np.uint8) * 50
        y_offset = 30
        cv2.putText(info_img, f"Cloth Type: {cloth_type}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 40
        
        if measurements:
            cv2.putText(info_img, f"Shoulder Width: {measurements.get('shoulder_width', 0):.1f}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 30
            cv2.putText(info_img, f"Torso Height: {measurements.get('torso_height', 0):.1f}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 30
            cv2.putText(info_img, f"Keypoints: {len(kps)}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 30
            cv2.putText(info_img, f"Polygon Points: {len(dst_poly) if dst_poly is not None else 0}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        debug_img[user_img.height:, user_img.width:] = info_img
        
        save_debug_image(Image.fromarray(debug_img), "comprehensive_debug.png")
        
    except Exception as e:
        print(f"⚠ Error creating debug visualization: {e}")

def resize_image_pil(img, max_size=1024):
    """Resizes a PIL image if it exceeds the maximum size."""
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img

def enhance_cloth_quality(cloth_img: Image.Image) -> Image.Image:
    """Enhances cloth image quality with improved color and detail preservation."""
    # Convert to RGBA if not already
    if cloth_img.mode != 'RGBA':
        cloth_img = cloth_img.convert('RGBA')
    
    # Enhance sharpness with more subtle adjustment
    enhancer = ImageEnhance.Sharpness(cloth_img)
    cloth_img = enhancer.enhance(1.3)
    
    # Enhance contrast with color preservation
    enhancer = ImageEnhance.Contrast(cloth_img)
    cloth_img = enhancer.enhance(1.15)
    
    # Fine-tune brightness
    enhancer = ImageEnhance.Brightness(cloth_img)
    cloth_img = enhancer.enhance(1.05)
    
    # Apply slight color enhancement
    enhancer = ImageEnhance.Color(cloth_img)
    cloth_img = enhancer.enhance(1.1)
    
    return cloth_img

def clean_cloth(cloth_img: Image.Image, cloth_type: str = "shirt") -> Image.Image:
    """Removes background & mannequin from a cloth image with improved precision."""
    print("🟢 Step 1: Cleaning and preparing cloth image...")
    
    # Resize while maintaining aspect ratio
    cloth_img = resize_image_pil(cloth_img, max_size=1024)
    
    # Enhance image quality
    cloth_img = enhance_cloth_quality(cloth_img)
    
    # Adjust contrast and brightness for better segmentation
    enhancer = ImageEnhance.Contrast(cloth_img)
    cloth_img = enhancer.enhance(1.2)  # Increase contrast
    enhancer = ImageEnhance.Brightness(cloth_img)
    cloth_img = enhancer.enhance(1.1)  # Slight brightness boost
    
    save_debug_image(cloth_img, "cloth_original.png")

    try:
        session = cloth_session if cloth_type.lower() in ["dress", "shirt", "top"] else None
        no_bg = remove(cloth_img, session=session)
        np_img = np.array(no_bg)
    except Exception as e:
        print(f"⚠ Background removal failed: {e}. Using original image.")
        np_img = np.array(cloth_img.convert('RGBA'))

    if np_img.shape[2] == 3: # Ensure RGBA
        alpha = np.full((np_img.shape[0], np_img.shape[1], 1), 255, dtype=np_img.dtype)
        np_img = np.concatenate([np_img, alpha], axis=2)

    save_debug_image(Image.fromarray(np_img), "cloth_after_bg_removal.png")

    # Additional cleaning for better quality
    try:
        # Remove skin tones if detected
        if cloth_type.lower() != "dress":
            hsv = cv2.cvtColor(np_img[:, :, :3], cv2.COLOR_RGB2HSV)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
            np_img[skin_mask > 0] = (0, 0, 0, 0)
    except Exception as e:
        print(f"⚠ Skin removal failed: {e}")

    return Image.fromarray(np_img, "RGBA")

def get_body_measurements(kps, idx_map):
    """Extract body measurements from keypoints with improved accuracy."""
    try:
        # Get key points with fallbacks
        left_shoulder = kps[idx_map.get("left_shoulder", 5)]
        right_shoulder = kps[idx_map.get("right_shoulder", 6)]
        left_hip = kps[idx_map.get("left_hip", 11)]
        right_hip = kps[idx_map.get("right_hip", 12)]
        
        # Calculate neck point more accurately
        mid_shoulder = (left_shoulder + right_shoulder) / 2
        neck = kps[idx_map.get("neck", 1)] if "neck" in idx_map else mid_shoulder - np.array([0, 20])
        
        # Calculate chest point (between neck and mid_shoulder)
        chest_point = (neck + mid_shoulder) / 2
        
        # Calculate measurements with scaling factors
        shoulder_width = np.linalg.norm(right_shoulder - left_shoulder) * 1.2  # Add 20% for clothing margin
        chest_width = shoulder_width * 0.95  # Chest slightly narrower than shoulders
        waist_width = np.linalg.norm(right_hip - left_hip) * 1.1  # Add 10% for clothing margin
        torso_height = np.linalg.norm(mid_shoulder - ((left_hip + right_hip) / 2)) * 1.05  # Add 5% for length
        
        # Calculate side points for better fitting
        left_side = (left_shoulder + left_hip) / 2
        right_side = (right_shoulder + right_hip) / 2
        
        return {
            "shoulder_width": shoulder_width,
            "chest_width": chest_width,
            "waist_width": waist_width,
            "torso_height": torso_height,
            "neck_point": neck,
            "chest_point": chest_point,
            "shoulder_points": (left_shoulder, right_shoulder),
            "hip_points": (left_hip, right_hip),
            "side_points": (left_side, right_side)
        }
    except Exception as e:
        print(f"❌ Error in get_body_measurements: {e}")
        raise

def recommend_size(measurements):
    """Recommend clothing size based on measurements."""
    shoulder_width = measurements["shoulder_width"]
    if shoulder_width < 130: 
        return "S"
    if shoulder_width < 160: 
        return "M"
    if shoulder_width < 190: 
        return "L"
    return "XL"

def create_realistic_polygon(measurements, cloth_type, user_img_shape):
    """Create a realistic polygon for mesh warping with precise shoulder alignment."""
    h, w = user_img_shape[:2]
    
    # Extract all measurements
    shoulder_w = measurements["shoulder_width"]
    chest_w = measurements["chest_width"]
    waist_w = measurements["waist_width"]
    torso_h = measurements["torso_height"]
    neck_point = measurements["neck_point"]
    chest_point = measurements["chest_point"]
    left_shoulder, right_shoulder = measurements["shoulder_points"]
    left_hip, right_hip = measurements["hip_points"]
    left_side, right_side = measurements["side_points"]
    
    # Adjust shoulder points for better alignment
    shoulder_offset = 10  # Pixels to extend shoulders slightly
    left_shoulder_adj = left_shoulder + np.array([-shoulder_offset, 0])
    right_shoulder_adj = right_shoulder + np.array([shoulder_offset, 0])
    
    # Calculate neck width and adjust neck point
    neck_width = np.linalg.norm(right_shoulder - left_shoulder) * 0.2  # 20% of shoulder width
    neck_height = 20  # Pixels above shoulders
    neck_point = (left_shoulder + right_shoulder) / 2 - np.array([0, neck_height])
    
    # Adjust chest points for better draping
    left_chest = chest_point + np.array([-chest_w/2.2, 0])  # Slightly narrower chest
    right_chest = chest_point + np.array([chest_w/2.2, 0])
    
    # Calculate control points for natural curves
    left_chest = chest_point + np.array([-chest_w/2, 0])
    right_chest = chest_point + np.array([chest_w/2, 0])
    
    # Create more natural curves for the sides
    # Create shoulder curves for better fitting
    left_shoulder_curve = np.array([
        neck_point + np.array([-neck_width/2, 0]),
        left_shoulder_adj,
        left_chest
    ])
    
    right_shoulder_curve = np.array([
        neck_point + np.array([neck_width/2, 0]),
        right_shoulder_adj,
        right_chest
    ])
    
    # Create side curves with better draping
    left_curve = np.array([
        left_chest,
        left_side + np.array([-15, 0]),  # Increased outward curve
        left_hip + np.array([-5, 0])  # Slight hip adjustment
    ])
    
    right_curve = np.array([
        right_chest,
        right_side + np.array([15, 0]),  # Increased outward curve
        right_hip + np.array([5, 0])  # Slight hip adjustment
    ])
    
    # Combine all points for the final polygon
    dst_poly = np.concatenate([
        [neck_point],
        left_shoulder_curve,
        left_curve,
        [left_hip],
        [right_hip],
        right_curve[::-1],  # Reverse right curve
        right_shoulder_curve[::-1],  # Reverse right shoulder curve
    ], axis=0).astype(np.float32)
    
    return dst_poly

def intelligent_size_scaling(cloth_img: Image.Image, measurements: dict, cloth_type: str) -> Image.Image:
    """Intelligently scale cloth based on body measurements and cloth type with improved accuracy."""
    try:
        cloth_w, cloth_h = cloth_img.size
        shoulder_width = measurements.get("shoulder_width", 100)
        torso_height = measurements.get("torso_height", 150)
        chest_width = measurements.get("chest_width", shoulder_width * 0.95)
        
        # Calculate target dimensions with more precise ratios for shirts
        if cloth_type.lower() == "dress":
            target_width = shoulder_width * 1.2  # Dresses are typically wider
            target_height = torso_height * 2.5   # Dresses are longer
        elif cloth_type.lower() in ["shirt", "top"]:
            # More precise shirt scaling
            target_width = max(shoulder_width * 1.05, chest_width * 1.1)  # Slightly wider than shoulders
            target_height = torso_height * 1.3   # Reduced height multiplier for better fit
            
            # Adjust width based on chest measurement
            if chest_width > shoulder_width:
                target_width = chest_width * 1.15
        else:  # pants
            target_width = shoulder_width * 0.8  # Pants are narrower at waist
            target_height = torso_height * 2.0   # Pants are longer
        
        # Calculate scale factors
        scale_x = target_width / cloth_w
        scale_y = target_height / cloth_h
        
        # Use the smaller scale to maintain aspect ratio
        scale = min(scale_x, scale_y)
        
        # Apply minimum and maximum scale limits
        scale = max(0.3, min(scale, 2.0))
        
        new_size = (int(cloth_w * scale), int(cloth_h * scale))
        return cloth_img.resize(new_size, Image.LANCZOS)
        
    except Exception as e:
        print(f"⚠ Error in intelligent_size_scaling: {e}")
        return cloth_img

def improved_overlay(user_img: Image.Image, cloth_img: Image.Image, cloth_type: str = "shirt", measurements: dict = None):
    """Improved fallback overlay method with intelligent positioning and scaling."""
    print("🟡 Running improved fallback overlay...")
    try:
        user_w, user_h = user_img.size
        
        # Use intelligent scaling if measurements are available
        if measurements:
            cloth_resized = intelligent_size_scaling(cloth_img, measurements, cloth_type)
        else:
            # Fallback to basic scaling
            scale_factor = (user_w * 0.5) / cloth_img.width
            new_size = (int(cloth_img.width * scale_factor), int(cloth_img.height * scale_factor))
            cloth_resized = cloth_img.resize(new_size, Image.LANCZOS)
        
        # Better positioning based on cloth type
        if cloth_type.lower() == "dress":
            # Dresses start higher and are centered
            y_offset = int(user_h * 0.15)
            x_offset = (user_w - cloth_resized.width) // 2
        elif cloth_type.lower() in ["shirt", "top"]:
            # Shirts start at shoulder level
            y_offset = int(user_h * 0.2)
            x_offset = (user_w - cloth_resized.width) // 2
        else:  # pants
            # Pants start at waist level
            y_offset = int(user_h * 0.4)
            x_offset = (user_w - cloth_resized.width) // 2
        
        # Ensure the cloth doesn't go outside image bounds
        x_offset = max(0, min(x_offset, user_w - cloth_resized.width))
        y_offset = max(0, min(y_offset, user_h - cloth_resized.height))
        
        # Apply slight rotation for more natural look
        if cloth_type.lower() in ["shirt", "top"]:
            # Slight rotation to match body posture
            cloth_rotated = cloth_resized.rotate(2, expand=True, fillcolor=(0, 0, 0, 0))
        else:
            cloth_rotated = cloth_resized
        
        # Create final image with better blending
        final = user_img.copy().convert("RGBA")
        
        # Apply soft edges to the cloth for better integration
        cloth_np = np.array(cloth_rotated)
        if cloth_np.shape[2] == 4:
            alpha = cloth_np[:, :, 3]
            alpha_blurred = cv2.GaussianBlur(alpha, (3, 3), 1.0)
            cloth_np[:, :, 3] = alpha_blurred
            cloth_rotated = Image.fromarray(cloth_np)
        
        final.paste(cloth_rotated, (x_offset, y_offset), cloth_rotated)
        return final
        
    except Exception as e:
        print(f"❌ Error in improved_overlay: {e}")
        # Return original user image as last resort
        return user_img.convert("RGBA")

def advanced_mesh_warp(src_img, src_poly, dst_poly, out_shape):
    """Perform advanced mesh warping using the ai_engine."""
    try:
        return warp_mesh.warp_rgba_mesh(np.array(src_img), src_poly, dst_poly, out_shape)
    except Exception as e:
        print(f"❌ Error in advanced_mesh_warp: {e}")
        raise

def enhanced_blend(user_img: Image.Image, warped: np.ndarray, person_mask: np.ndarray = None, 
                clothing_mask: np.ndarray = None) -> Image.Image:
    """Enhanced blending of warped cloth onto user image with realistic integration."""
    try:
        print("✨ Applying enhanced blending with clothing replacement...")
        
        # Convert to numpy arrays for processing
        user_np = np.array(user_img.convert("RGBA"))
        warped_np = warped.astype(np.float32)
        h, w = user_np.shape[:2]
        
        # Create base alpha channel
        alpha = warped_np[:, :, 3] / 255.0
        
        # Enhanced edge processing
        alpha_blurred = cv2.GaussianBlur(alpha, (3, 3), 0.8)  # Reduced blur for sharper edges
        
        # Create detailed edge mask for better transitions
        edge_detector = cv2.Canny((alpha_blurred * 255).astype(np.uint8), 50, 150)
        edge_mask = cv2.dilate(edge_detector, np.ones((3, 3), np.uint8), iterations=1)
        edge_blend = cv2.GaussianBlur(edge_mask.astype(float) / 255.0, (5, 5), 1.0)
        
        # Use person segmentation mask to improve blending if available
        if person_mask is not None:
            # Scale person mask to match image size
            person_mask = cv2.resize(person_mask, (user_np.shape[1], user_np.shape[0]))
            # Use person mask to refine alpha channel
            alpha_blurred = alpha_blurred * (person_mask / 255.0)
        
        # Use clothing mask to ensure proper replacement
        if clothing_mask is not None:
            # Scale clothing mask to match image size
            clothing_mask = cv2.resize(clothing_mask, (user_np.shape[1], user_np.shape[0]))
            # Create refined mask for clothing region
            refined_mask = cv2.GaussianBlur(clothing_mask.astype(float) / 255.0, (5, 5), 1.0)
            # Enhance alpha in clothing region with smooth transition
            alpha_blurred = cv2.addWeighted(alpha_blurred, 0.7, refined_mask, 0.3, 0)
        
        # Apply edge-aware blending
        edge_mask = cv2.Canny((alpha_blurred * 255).astype(np.uint8), 50, 150)
        edge_mask = cv2.dilate(edge_mask, np.ones((3, 3), np.uint8), iterations=1)
        edge_mask_soft = cv2.GaussianBlur(edge_mask.astype(float) / 255.0, (5, 5), 1.0)
        
        # Combine all masks for final blending
        final_alpha = alpha_blurred * (1 - edge_mask_soft * 0.5)
        
        # Create the blended image
        blended = np.zeros_like(user_np, dtype=np.float32)
        for c in range(3):
            blended[:, :, c] = (user_np[:, :, c] * (1 - final_alpha) + 
                               warped_np[:, :, c] * final_alpha)
        blended[:, :, 3] = (user_np[:, :, 3] * (1 - final_alpha) + 
                           warped_np[:, :, 3] * final_alpha)
        
        return Image.fromarray(blended.astype(np.uint8))
        
    except Exception as e:
        print(f"❌ Error in enhanced_blend: {e}")
        return user_img

# --- Main Process ---

def tryon_process(user_img_source: str, cloth_img_source: str, cloth_type: str = "shirt"):
    """
    Main virtual try-on function. Accepts either local paths or URLs for images.
    """
    print("🟢 Starting virtual try-on process...")
    
    # Initialize variables
    user_img = None
    cloth_img = None
    cloth_segmenter = None
    clothing_mask = None
    body_bbox = None
    final = None
    preferred_size = None
    temp_files = []  # Track temporary files for cleanup
    
    # Set processing limits
    MAX_IMAGE_SIZE = 1024  # Maximum dimension for processing
    MIN_IMAGE_SIZE = 256   # Minimum dimension required

    try:
        # Step 1: Get local image paths (downloads from URL if necessary)
        user_img_path = get_image_path(user_img_source, "user")
        cloth_img_path = get_image_path(cloth_img_source, "cloth")

        print(f"📥 Loading images: user='{user_img_path}', cloth='{cloth_img_path}'")
        
        # Load and validate images
        from . import image_utils
        try:
            user_img = Image.open(user_img_path)
            user_img = image_utils.validate_and_preprocess_image(user_img, MIN_IMAGE_SIZE, MAX_IMAGE_SIZE)
            
            cloth_img = Image.open(cloth_img_path)
            cloth_img = image_utils.validate_and_preprocess_image(cloth_img, MIN_IMAGE_SIZE, MAX_IMAGE_SIZE)
            
            print(f"✅ Images loaded and validated - User: {user_img.size}, Cloth: {cloth_img.size}")
        except Exception as e:
            raise RuntimeError(f"Image validation failed: {str(e)}")

        # Step 1.5: Segment and remove existing clothing
        print("🔍 Segmenting existing clothing...")
        from . import segmentation
        cloth_segmenter = segmentation.ClothSegmentation()
        
        # Convert to OpenCV format for processing
        user_cv = cv2.cvtColor(np.array(user_img), cv2.COLOR_RGBA2BGR)
        
        # Get clothing mask and body region
        clothing_mask, body_bbox = cloth_segmenter.segment_clothing(user_img_path)
        if clothing_mask is None:
            print("⚠ Warning: Could not detect clothing region, falling back to basic processing")
            clothing_mask = np.ones((user_cv.shape[0], user_cv.shape[1]), dtype=np.uint8) * 255
            
            # Remove existing clothing with more robust error handling
            try:
                user_no_cloth = cloth_segmenter.remove_existing_clothing(user_cv, clothing_mask)
                user_img = Image.fromarray(cv2.cvtColor(user_no_cloth, cv2.COLOR_BGR2RGBA))
                save_debug_image(user_img, "user_no_clothing.png")
            except Exception as e:
                print(f"⚠ Warning: Error removing existing clothing: {e}")
                user_img = Image.fromarray(cv2.cvtColor(user_cv, cv2.COLOR_BGR2RGBA))
            
            # Get person segmentation for fitting
            try:
                from . import human_parsing
                person_mask = human_parsing.infer_person_mask(user_img_path, thresh=0.6)
            except Exception as e:
                print(f"⚠ Warning: Error getting person mask: {e}")
                person_mask = None        # Step 2: Clean cloth image
        print("🧹 Cleaning cloth...")
        cloth_clean = clean_cloth(cloth_img, cloth_type)

        preferred_size = None
        final = None

        # Step 3: Process pose, measurements, and warping
        pose_result = None
        try:
            print("🔍 Detecting pose and processing measurements...")
            pose_result = person_pose.infer_keypoints(user_img_path)
            
            if not pose_result or "kps" not in pose_result or len(pose_result["kps"]) < 5:
                print("⚠ Warning: Insufficient pose keypoints detected")
                raise RuntimeError("Insufficient keypoints for advanced processing")
                
            kps, idx_map = pose_result["kps"], pose_result["index_map"]
            print(f"✅ Detected {len(kps)} keypoints")
            
            # Calculate measurements and get size recommendation
            measurements = get_body_measurements(kps, idx_map)
            preferred_size = recommend_size(measurements)
            print(f"📏 Recommended size: {preferred_size}")
            
            # Create warping polygon
            dst_poly = create_realistic_polygon(measurements, cloth_type, np.array(user_img).shape)
            
            # Debug visualization
            debug_user = np.array(user_img.copy())
            for i, (x, y) in enumerate(dst_poly.astype(int)):
                color = (0, 255, 0) if i < 2 else (255, 0, 0) if i < 4 else (0, 0, 255)
                cv2.circle(debug_user, (int(x), int(y)), 8, color, -1)
                cv2.putText(debug_user, str(i), (int(x)+10, int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.polylines(debug_user, [dst_poly.astype(int)], isClosed=True, color=(255, 255, 0), thickness=2)
            save_debug_image(Image.fromarray(debug_user), "polygon_debug.png")            # Step 4: Calculate measurements and polygons
            measurements = get_body_measurements(kps, idx_map)
            preferred_size = recommend_size(measurements)
            dst_poly = create_realistic_polygon(measurements, cloth_type, np.array(user_img).shape)
            
            # Create comprehensive debug visualization
            create_debug_visualization(user_img, cloth_clean, kps, idx_map, measurements, dst_poly, cloth_type)
            
            # Debug: Save polygon visualization
            debug_user = np.array(user_img.copy())
            for i, (x, y) in enumerate(dst_poly.astype(int)):
                color = (0, 255, 0) if i < 2 else (255, 0, 0) if i < 4 else (0, 0, 255)
                cv2.circle(debug_user, (int(x), int(y)), 8, color, -1)
                cv2.putText(debug_user, str(i), (int(x)+10, int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.polylines(debug_user, [dst_poly.astype(int)], isClosed=True, color=(255, 255, 0), thickness=2)
            save_debug_image(Image.fromarray(debug_user), "polygon_debug.png")
            
            Hc, Wc = np.array(cloth_clean).shape[:2]

            # Build a reasonable source polygon based on the cloth image and resample
            # it to have the same number of points as the destination polygon to avoid
            # index errors during triangulation/warping.
            try:
                num_dst = int(dst_poly.shape[0]) if dst_poly is not None else 4
            except Exception:
                num_dst = 4

            try:
                src_pts = fit_polygons.get_source_points(cloth_clean, n_points=num_dst)
                if src_pts is None or len(src_pts) < 3:
                    # fallback rectangle corners
                    src_pts = np.array([[0, 0], [Wc - 1, 0], [Wc - 1, Hc - 1], [0, Hc - 1]], dtype=np.float32)
            except Exception as e:
                print(f"⚠ Warning: get_source_points failed: {e}")
                src_pts = np.array([[0, 0], [Wc - 1, 0], [Wc - 1, Hc - 1], [0, Hc - 1]], dtype=np.float32)

            # Step 5: Warp and blend
            print("🌊 Performing mesh warping...")
            # Perform warping with error handling
            try:
                warped = advanced_mesh_warp(cloth_clean, src_pts, dst_poly, (user_img.height, user_img.width))
                save_debug_image(Image.fromarray(warped), "cloth_warped.png")

                print("🎨 Applying enhanced blending with segmentation masks...")
                final = enhanced_blend(user_img, warped, person_mask, clothing_mask)
                save_debug_image(final, "final_blended.png")
            except Exception as e:
                print(f"⚠ Warning: Error in warping/blending: {e}")
                print("Falling back to basic overlay...")
                final = improved_overlay(user_img, cloth_clean, cloth_type, measurements)

        except Exception as pose_e:
            print(f"⚠ Advanced pipeline failed: {pose_e}. Using improved fallback overlay.")
            # Try to get measurements even if pose detection partially failed
            measurements = None
            try:
                if 'measurements' in locals():
                    measurements = measurements
                elif 'kps' in locals() and 'idx_map' in locals():
                    measurements = get_body_measurements(kps, idx_map)
            except:
                pass
            
            final = improved_overlay(user_img, cloth_clean, cloth_type, measurements)
            if preferred_size is None:
                preferred_size = "M"  # Default size on fallback

        # Step 6: Encode final image to Base64
        print("💾 Encoding final image...")
        try:
            # Ensure we have a valid image to encode
            if final is None:
                raise ValueError("No image to encode")
                
            # Convert to RGB to ensure compatibility
            final = final.convert('RGB')
            
            # Create a buffer and save the image
            buf = io.BytesIO()
            final.save(buf, format="PNG", quality=95)
            buf.seek(0)  # Reset buffer position
            
            # Encode to base64 with proper formatting
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            result = {
                "output_image_base64": f"data:image/png;base64,{img_str}",
                "preferred_size": preferred_size or "M"
            }
            
            print("✅ Try-on process completed successfully!")
            return result
            
        except Exception as e:
            print(f"❌ Error during image encoding: {e}")
            raise RuntimeError(f"Failed to encode output image: {str(e)}")

    except Exception as e:
        print(f"❌ Critical error in tryon_process: {e}")
        import traceback
        traceback.print_exc()
        
        # Ensure we return a properly formatted error response
        error_msg = str(e)
        try:
            # Try to create a basic error image with text
            error_img = Image.new('RGB', (400, 200), color='white')
            d = ImageDraw.Draw(error_img)
            d.text((10, 10), f"Error: {error_msg}", fill='black')
            
            # Convert error image to base64
            buf = io.BytesIO()
            error_img.save(buf, format="PNG")
            buf.seek(0)
            error_img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            return {
                "output_image_base64": f"data:image/png;base64,{error_img_str}",
                "error": error_msg
            }
        except:
            # If even creating error image fails, return minimal response
            return {
                "output_image_base64": "",
                "error": error_msg
            }

# --- Module Sanity Check ---
try:
    if 'tryon_process' in globals() and callable(globals()['tryon_process']):
        print("✅ Sanity Check Passed: 'tryon_process' is defined and callable in this module.")
    else:
        print("❌ Sanity Check FAILED: 'tryon_process' is NOT defined or is not a function in this module's scope!")
except Exception as e:
    print(f"ERROR during sanity check: {e}")

print("✅ Virtual Try-On Engine module loaded. 'tryon_process' function is now available for import.")