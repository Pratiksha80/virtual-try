import os
import io
import cv2
import base64
import numpy as np
from PIL import Image
import rembg
from rembg import remove
import person_pose
import fit_polygons
import warp_mesh

cloth_session = rembg.new_session("u2net_cloth_seg")

DEBUG_DIR = "uploads/debug"
os.makedirs(DEBUG_DIR, exist_ok=True)


def save_debug_image(img_pil, name):
    try:
        path = os.path.join(DEBUG_DIR, name)
        img_pil.save(path)
        print(f"🖼 Saved debug image: {path}")
    except Exception as e:
        print(f"⚠ Could not save debug image {name}: {e}")


def resize_image_pil(img, max_size=800):
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    return img


def clean_cloth(cloth_img: Image.Image, cloth_type: str = "shirt") -> Image.Image:

    """Remove background & mannequin."""
    print("🟢 Step 1: Cleaning cloth image...")
    cloth_img = resize_image_pil(cloth_img, max_size=800)

    try:
        no_bg = remove(cloth_img, session=cloth_session if cloth_type.lower() == "dress" else None)
        np_img = np.array(no_bg)
    except Exception as e:
        print("⚠ Background removal failed:", e)
        np_img = np.array(cloth_img)

    save_debug_image(Image.fromarray(np_img), "cloth_clean.png")

    # Remove mannequin skin
    try:
        if np_img.shape[2] == 4:
            bgr = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
        else:
            bgr = np_img

        if cloth_type.lower() != "dress":
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 30, 60], dtype=np.uint8)
            upper_skin = np.array([25, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            np_img[mask > 0] = (0, 0, 0, 0)
    except Exception as e:
        print("⚠ Mannequin cleaning failed:", e)

    return Image.fromarray(np_img, "RGBA")


def recommend_size(kps, idx_map):
    """Estimate preferred size from body keypoints (shoulder width)."""
    ls = kps[idx_map["left_shoulder"]]
    rs = kps[idx_map["right_shoulder"]]
    shoulder_width = np.linalg.norm(rs - ls)

    if shoulder_width < 120:
        return "S"
    elif shoulder_width < 180:
        return "M"
    elif shoulder_width < 240:
        return "L"
    else:
        return "XL"


def basic_overlay(user_img: Image.Image, cloth_img: Image.Image) -> Image.Image:
    """Fallback overlay if pose fails."""
    print("🟡 Running basic overlay...")
    user_w, user_h = user_img.size

    torso_top = int(user_h * 0.20)
    torso_bottom = int(user_h * 0.55)
    torso_height = torso_bottom - torso_top
    torso_width = int(user_w * 0.5)

    cloth_resized = cloth_img.resize((torso_width, torso_height), Image.LANCZOS)

    x = (user_w - torso_width) // 2
    y = torso_top

    final = user_img.copy()
    final.paste(cloth_resized, (x, y), cloth_resized)

    save_debug_image(final, "final_fallback.png")
    return final


def smooth_blend(user_img: Image.Image, warped: np.ndarray) -> Image.Image:
    """Blend cloth smoothly with alpha mask."""
    print("✨ Applying smooth blending...")
    warped_alpha = warped[:, :, 3]
    warped_rgb = warped[:, :, :3]

    # Blur alpha for soft edges
    blurred_alpha = cv2.GaussianBlur(warped_alpha, (21, 21), 10)

    # Normalize
    alpha_f = blurred_alpha.astype(np.float32) / 255.0
    rgb_f = warped_rgb.astype(np.float32) / 255.0

    user_np = np.array(user_img).astype(np.float32) / 255.0

    blended = user_np[:, :, :3] * (1 - alpha_f[..., None]) + rgb_f * alpha_f[..., None]
    blended = (blended * 255).astype(np.uint8)

    return Image.fromarray(blended)


def _tight_bbox_from_alpha(np_rgba: np.ndarray):
    """Return tight bounding box (xmin, ymin, xmax, ymax) of non-zero alpha.
    Falls back to full image if no alpha channel or empty mask.
    """
    if np_rgba.ndim == 3 and np_rgba.shape[2] == 4:
        alpha = np_rgba[:, :, 3]
        ys, xs = np.where(alpha > 5)
        if ys.size > 0 and xs.size > 0:
            return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    # fallback to full image
    h, w = np_rgba.shape[:2]
    return 0, 0, w - 1, h - 1


def tryon_process(user_img_path: str, cloth_img_path: str, cloth_type: str = "shirt"):
    print("🟢 Starting try-on process...")
    cloth_type = cloth_type.strip().lower()

    user_img = Image.open(user_img_path).convert("RGBA")
    orig_w, orig_h = user_img.size
    # Speed-up and stability: process at a reasonable resolution
    max_side = 1024
    if max(orig_w, orig_h) > max_side:
        scale = max_side / float(max(orig_w, orig_h))
        proc_w, proc_h = int(orig_w * scale), int(orig_h * scale)
        user_img_proc = user_img.resize((proc_w, proc_h), Image.LANCZOS)
        user_img_for_pose_path = user_img_path
        # Save a temporary resized copy for pose to ensure consistent coordinates
        tmp_proc_path = os.path.join(DEBUG_DIR, "_tmp_user_pose.png")
        user_img_proc.save(tmp_proc_path)
        user_img_for_pose_path = tmp_proc_path
    else:
        user_img_proc = user_img
        user_img_for_pose_path = user_img_path
    cloth_img = Image.open(cloth_img_path).convert("RGBA")

    # 1. Clean cloth
    cloth_clean = clean_cloth(cloth_img, cloth_type)

    preferred_size = None  # default

    try:
        # 2. Pose
        pose = person_pose.infer_keypoints(user_img_for_pose_path)
        if not pose or "kps" not in pose:
            raise RuntimeError("Pose model returned empty")
        kps, idx_map = pose["kps"], pose["index_map"]

        # 👕 Size recommendation
        preferred_size = recommend_size(kps, idx_map)

        # 3. Compute a robust torso quad for warping (prevents misalignment)
        ls = kps[idx_map["left_shoulder"]]
        rs = kps[idx_map["right_shoulder"]]
        ms = kps[idx_map["mid_shoulder"]]
        mh = kps[idx_map["mid_hip"]]
        # Work in processed scale
        shoulder_width = float(np.linalg.norm(rs - ls))
        torso_len = float(np.linalg.norm(mh - ms)) * 0.95
        # Vertical direction from shoulders to hips
        v_dir = mh - ms
        v_norm = v_dir / (np.linalg.norm(v_dir) + 1e-6)
        # Top corners use actual shoulders; bottoms are shifted down by torso length
        top_left = ls
        top_right = rs
        bottom_left = ls + v_norm * torso_len
        bottom_right = rs + v_norm * torso_len
        dst_quad = np.stack([top_left, top_right, bottom_right, bottom_left], axis=0).astype(np.float32)

        # 🔎 DEBUG: Draw quad on body
        dbg_user = np.array(user_img_proc.copy())
        for (x, y) in dst_quad.astype(int):
            cv2.circle(dbg_user, (int(x), int(y)), 6, (0, 255, 0), -1)
        cv2.polylines(dbg_user, [dst_quad.astype(int)], isClosed=True, color=(0, 0, 255), thickness=3)
        save_debug_image(Image.fromarray(dbg_user), "polygon_debug.png")

        # 4. Warp
        src_np = np.array(cloth_clean)
        # Crop to tight cloth bbox to avoid margins affecting scale
        xmin, ymin, xmax, ymax = _tight_bbox_from_alpha(src_np)
        src_np_cropped = src_np[ymin:ymax+1, xmin:xmax+1]
        Hc, Wc = src_np_cropped.shape[:2]
        src_pts = np.array([[0, 0], [Wc, 0], [Wc, Hc], [0, Hc]], dtype=np.float32)
        dst_pts = dst_quad

        warped = warp_mesh.warp_rgba_mesh(
            src_np_cropped,
            src_pts=src_pts,
            dst_pts=dst_pts,
            out_shape=(user_img_proc.height, user_img_proc.width),
        )
        save_debug_image(Image.fromarray(warped), "cloth_warped.png")

        # 5. Blend
        final = smooth_blend(user_img_proc, warped)
        save_debug_image(final, "final_output.png")

    except Exception as e:
        print("⚠ Advanced pipeline failed, fallback:", e)
        final = basic_overlay(user_img, cloth_clean)

    # Encode final image
    buf = io.BytesIO()
    final.save(buf, format="PNG")

    return {
        "output_image_base64": base64.b64encode(buf.getvalue()).decode("utf-8"),
        "preferred_size": preferred_size
    }

