# backend/ai_engine/tryon_processor.py
import io
import base64
import os
from PIL import Image
from rembg import remove, new_session
import cv2
import numpy as np
import mediapipe as mp

# Paths
DEBUG_DIR = "uploads/debug"
os.makedirs(DEBUG_DIR, exist_ok=True)

# Load cloth segmentation model
cloth_session = new_session("u2net_cloth_seg")
mp_pose = mp.solutions.pose


def save_debug_image(img_pil, name):
    """Save debug images for inspection."""
    path = os.path.join(DEBUG_DIR, name)
    img_pil.save(path)
    print(f"🖼️ Saved debug image: {path}")


def resize_image_cv2(img, max_size=800):
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        return cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


def resize_image_pil(img, max_size=800):
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img


def clean_cloth(cloth_img: Image.Image, cloth_type: str = "shirt") -> Image.Image:
    print("🟢 Step 1: Cleaning cloth image...")
    cloth_img = resize_image_pil(cloth_img, max_size=800)

    # Remove background
    print("   ➡ Removing background...")
    if cloth_type.lower() == "dress":
        no_bg = remove(cloth_img, session=cloth_session)
    else:
        no_bg = remove(cloth_img)
    np_img = np.array(no_bg)

    save_debug_image(Image.fromarray(np_img), "cloth_clean.png")

    # Remove mannequin skin
    print("   ➡ Removing mannequin skin...")
    if np_img.shape[2] == 4:
        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
    else:
        bgr = np_img

    if cloth_type.lower() != "dress":
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower_skin1 = np.array([0, 30, 60], dtype=np.uint8)
        upper_skin1 = np.array([25, 255, 255], dtype=np.uint8)
        lower_skin2 = np.array([0, 15, 0], dtype=np.uint8)
        upper_skin2 = np.array([30, 200, 200], dtype=np.uint8)
        skin_mask = cv2.bitwise_or(cv2.inRange(hsv, lower_skin1, upper_skin1),
                                   cv2.inRange(hsv, lower_skin2, upper_skin2))
        np_img[skin_mask > 0] = (0, 0, 0, 0)

    return Image.fromarray(np_img, "RGBA")


def get_body_measurements(user_img_path: str):
    print("🟢 Step 2: Extracting body measurements...")
    img = cv2.imread(user_img_path)
    img = resize_image_cv2(img, max_size=800)

    h, w = img.shape[:2]
    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            print("⚠️ Pose landmarks not detected, using fallback values.")
            return int(h * 0.25), int(h * 0.55), int(h * 0.95), int(w * 0.5), None

        lm = results.pose_landmarks.landmark
        shoulder_y = int(min(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y,
                             lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y) * h)
        hip_y = int(max(lm[mp_pose.PoseLandmark.LEFT_HIP].y,
                        lm[mp_pose.PoseLandmark.RIGHT_HIP].y) * h)
        ankle_y = int(max(lm[mp_pose.PoseLandmark.LEFT_ANKLE].y,
                          lm[mp_pose.PoseLandmark.RIGHT_ANKLE].y) * h)
        shoulder_width = int(abs(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x -
                                 lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].x) * w)

        print(f"   Measurements: shoulder_y={shoulder_y}, hip_y={hip_y}, ankle_y={ankle_y}, shoulder_width={shoulder_width}")
        return shoulder_y, hip_y, ankle_y, shoulder_width, results.pose_landmarks


def tryon_process(user_img_path: str, cloth_img_path: str, cloth_type: str = "shirt"):
    print("🟢 Step 0: Starting try-on process...")
    cloth_type = cloth_type.strip().lower()

    user_img = Image.open(user_img_path).convert("RGBA")
    cloth_img = Image.open(cloth_img_path).convert("RGBA")

    # Clean cloth
    cloth_clean = clean_cloth(cloth_img, cloth_type)

    # Get body measurements
    shoulder_y, hip_y, ankle_y, shoulder_width, pose_landmarks = get_body_measurements(user_img_path)

    print("🟢 Step 3: Scaling and aligning clothing...")

    if cloth_type == "shirt":
        target_width = max(250, int(shoulder_width * 1.5))
        scale_ratio = target_width / max(1, cloth_clean.width)
        target_height = max(200, int(cloth_clean.height * scale_ratio))
        pos_y = shoulder_y

    elif cloth_type == "pant":
        target_height = max(400, ankle_y - hip_y)
        scale_ratio = target_height / max(1, cloth_clean.height)
        target_width = max(200, int(cloth_clean.width * scale_ratio))
        pos_y = hip_y

    elif cloth_type == "dress":
        target_height = max(600, ankle_y - shoulder_y)
        scale_ratio = target_height / max(1, cloth_clean.height)
        target_width = max(300, int(cloth_clean.width * scale_ratio))
        pos_y = shoulder_y

    else:
        raise ValueError("cloth_type must be 'shirt', 'pant', or 'dress'")

    cloth_resized = cloth_clean.resize((target_width, target_height), Image.LANCZOS)
    save_debug_image(cloth_resized, "cloth_resized.png")

    pos_x = user_img.width // 2 - cloth_resized.width // 2
    print(f"   ➡ Placing cloth at: ({pos_x}, {pos_y}), size=({target_width}, {target_height})")

    # Composite
    final_img = user_img.copy()
    final_img.paste(cloth_resized, (pos_x, pos_y), cloth_resized)
    save_debug_image(final_img, "final_output.png")

    # Encode
    print("🟢 Step 4: Encoding final image...")
    buffer = io.BytesIO()
    final_img.save(buffer, format="PNG")
    final_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    print("✅ Try-on complete!")
    return {"output_image_base64": final_b64}
