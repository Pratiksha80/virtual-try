# backend/ai_engine/fit_polygons.py
import numpy as np

def _pt(kps, idx_map, name):
    return kps[idx_map[name]] if name in idx_map else None

def target_poly_shirt(kps: np.ndarray, idx_map: dict) -> np.ndarray:
    # Get all required keypoints with enhanced shoulder detection
    ls = _pt(kps, idx_map, "left_shoulder")
    rs = _pt(kps, idx_map, "right_shoulder")
    mh = _pt(kps, idx_map, "mid_hip")
    ms = _pt(kps, idx_map, "mid_shoulder")
    le = _pt(kps, idx_map, "left_elbow")
    re = _pt(kps, idx_map, "right_elbow")
    lw = _pt(kps, idx_map, "left_wrist")
    rw = _pt(kps, idx_map, "right_wrist")
    
    # Get neck points for better shoulder line
    neck = _pt(kps, idx_map, "nose")  # Use nose as reference for neck position
    if neck is not None:
        neck_y = neck[1] + (ms[1] - neck[1]) * 0.3  # Adjust neck point down
        neck = np.array([ms[0], neck_y])
    
    if any(x is None for x in [ls, rs, mh, ms]):
        raise ValueError("missing keypoints for shirt")

    # Calculate body proportions with better scaling
    shoulder_width = np.linalg.norm(rs - ls)
    body_height = np.linalg.norm(mh - ms)
    
    # Calculate shoulder slope for natural fit
    shoulder_slope_left = np.arctan2(neck[1] - ls[1], neck[0] - ls[0])
    shoulder_slope_right = np.arctan2(neck[1] - rs[1], neck[0] - rs[0])
    
    # Adjust shoulders to follow natural body line
    shoulder_expand = shoulder_width * 0.03  # Further reduced for exact fit
    left_shoulder = ls + np.array([
        -shoulder_expand * np.cos(shoulder_slope_left),
        -shoulder_expand * np.sin(shoulder_slope_left)
    ])
    right_shoulder = rs + np.array([
        shoulder_expand * np.cos(shoulder_slope_right),
        -shoulder_expand * np.sin(shoulder_slope_right)
    ])
    
    # Enhanced armpit positioning with body curvature
    armpit_depth = shoulder_width * 0.1  # Tighter fit
    armpit_drop = shoulder_width * 0.15  # Vertical drop for natural draping
    left_armpit = ls + np.array([-armpit_depth, armpit_drop])
    right_armpit = rs + np.array([armpit_depth, armpit_drop])
    
    # Enhanced sleeve positioning with natural arm angles
    if all(x is not None for x in [le, re, lw, rw]):
        # Calculate actual arm angles from body
        left_arm_angle = np.arctan2(le[1] - ls[1], le[0] - ls[0])
        right_arm_angle = np.arctan2(re[1] - rs[1], re[0] - rs[0])
        
        # Calculate optimal sleeve position based on arm pose
        left_sleeve_vector = le - ls
        right_sleeve_vector = re - rs
        
        # Normalize and scale for better fit
        left_sleeve_length = min(np.linalg.norm(left_sleeve_vector) * 0.35,
                               shoulder_width * 0.4)
        right_sleeve_length = min(np.linalg.norm(right_sleeve_vector) * 0.35,
                                shoulder_width * 0.4)
        
        # Calculate normalized sleeve directions
        if np.linalg.norm(left_sleeve_vector) > 0:
            left_sleeve_dir = left_sleeve_vector / np.linalg.norm(left_sleeve_vector)
        else:
            left_sleeve_dir = np.array([-np.cos(np.pi/6), np.sin(np.pi/6)])
            
        if np.linalg.norm(right_sleeve_vector) > 0:
            right_sleeve_dir = right_sleeve_vector / np.linalg.norm(right_sleeve_vector)
        else:
            right_sleeve_dir = np.array([np.cos(np.pi/6), np.sin(np.pi/6)])
        
        # Set sleeve endpoints
        left_sleeve_mid = ls + left_sleeve_dir * left_sleeve_length
        right_sleeve_mid = rs + right_sleeve_dir * right_sleeve_length
        
        # Calculate adaptive sleeve width based on arm pose
        left_arm_thickness = min(np.linalg.norm(le - ls) * 0.1,
                               shoulder_width * 0.08)
        right_arm_thickness = min(np.linalg.norm(re - rs) * 0.1,
                                shoulder_width * 0.08)
        
        # Add sleeve width perpendicular to arm direction
        left_arm_dir = le - ls
        right_arm_dir = re - rs
        if np.linalg.norm(left_arm_dir) > 0:
            left_perp = np.array([-left_arm_dir[1], left_arm_dir[0]]) / np.linalg.norm(left_arm_dir)
        else:
            left_perp = np.array([0, 1])
        if np.linalg.norm(right_arm_dir) > 0:
            right_perp = np.array([-right_arm_dir[1], right_arm_dir[0]]) / np.linalg.norm(right_arm_dir)
        else:
            right_perp = np.array([0, 1])
        
        left_sleeve_top = left_sleeve_mid + left_perp * left_arm_thickness
        left_sleeve_bottom = left_sleeve_mid - left_perp * left_arm_thickness
        right_sleeve_top = right_sleeve_mid + right_perp * right_arm_thickness
        right_sleeve_bottom = right_sleeve_mid - right_perp * right_arm_thickness
    else:
        # Fallback to estimated sleeve positions with better angles
        arm_angle = 25 * np.pi / 180  # Slightly less steep
        sleeve_length = shoulder_width * 0.7  # More proportional
        
        left_sleeve_mid = ls + np.array([-np.cos(arm_angle), np.sin(arm_angle)]) * sleeve_length
        right_sleeve_mid = rs + np.array([np.cos(arm_angle), np.sin(arm_angle)]) * sleeve_length
        
        sleeve_width = shoulder_width * 0.12
        left_sleeve_top = left_sleeve_mid + np.array([0, -sleeve_width])
        left_sleeve_bottom = left_sleeve_mid + np.array([0, sleeve_width])
        right_sleeve_top = right_sleeve_mid + np.array([0, -sleeve_width])
        right_sleeve_bottom = right_sleeve_mid + np.array([0, sleeve_width])

    # Create more natural waistline with better proportions
    waist_curve = shoulder_width * 0.08
    hem_left = mh + (ls - ms) * 0.1 + np.array([-waist_curve, 0])
    hem_mid = mh + np.array([0, waist_curve * 0.5])  # Slight curve
    hem_right = mh + (rs - ms) * 0.1 + np.array([waist_curve, 0])

    # Create complete polygon with enhanced natural fit and interpolated points
    # Add intermediate points for smoother shoulder curve
    left_shoulder_mid = ls + (left_shoulder - ls) * 0.5
    right_shoulder_mid = rs + (right_shoulder - rs) * 0.5
    
    # Create smooth transition points for better draping
    left_transition = left_armpit + (left_shoulder - left_armpit) * 0.3
    right_transition = right_armpit + (right_shoulder - right_armpit) * 0.3
    
    poly = np.stack([
        left_shoulder, left_shoulder_mid, ls, rs, right_shoulder_mid, right_shoulder,  # Enhanced shoulder line
        right_sleeve_top, right_sleeve_bottom,  # Right sleeve
        right_transition, right_armpit,         # Smooth right transition
        hem_right, hem_mid, hem_left,          # Bottom hem
        left_armpit, left_transition,          # Smooth left transition
        left_sleeve_bottom, left_sleeve_top     # Left sleeve
    ], axis=0).astype(np.float32)
    
    return poly

def target_poly_pant(kps: np.ndarray, idx_map: dict) -> np.ndarray:
    lh = _pt(kps, idx_map, "left_hip")
    rh = _pt(kps, idx_map, "right_hip")
    lk = _pt(kps, idx_map, "left_knee")
    rk = _pt(kps, idx_map, "right_knee")
    la = _pt(kps, idx_map, "left_ankle")
    ra = _pt(kps, idx_map, "right_ankle")
    if any(x is None for x in [lh,rh,lk,rk,la,ra]):
        raise ValueError("missing keypoints for pant")
    waist_left, waist_right = lh, rh
    crotch = (lh + rh) / 2 + ( (lk+rk)/2 - (lh+rh)/2 ) * 0.15
    # left leg path
    left_poly  = np.stack([waist_left, crotch*0+waist_left*0+waist_left, lk, la], axis=0).astype(np.float32)
    # right leg path
    right_poly = np.stack([waist_right, crotch, rk, ra], axis=0).astype(np.float32)
    # we’ll densify later when sampling along edges
    return np.concatenate([left_poly, right_poly], axis=0)

def target_poly_dress(kps: np.ndarray, idx_map: dict) -> np.ndarray:
    ls = _pt(kps, idx_map, "left_shoulder")
    rs = _pt(kps, idx_map, "right_shoulder")
    ms = _pt(kps, idx_map, "mid_shoulder")
    la = _pt(kps, idx_map, "left_ankle")
    ra = _pt(kps, idx_map, "right_ankle")
    mh = _pt(kps, idx_map, "mid_hip")
    lh = _pt(kps, idx_map, "left_hip")
    rh = _pt(kps, idx_map, "right_hip")
    
    if any(x is None for x in [ls, rs, ms, la, ra, mh]):
        raise ValueError("missing keypoints for dress")
    
    # Calculate shoulder width for better proportions
    shoulder_width = np.linalg.norm(rs - ls)
    
    # More natural shoulder positioning
    shoulder_expand = shoulder_width * 0.06
    left_shoulder = ls + np.array([-shoulder_expand, 0])
    right_shoulder = rs + np.array([shoulder_expand, 0])
    
    # Better waist positioning using hip points if available
    if lh is not None and rh is not None:
        waist_left = lh + np.array([-shoulder_width * 0.05, 0])
        waist_right = rh + np.array([shoulder_width * 0.05, 0])
    else:
        waist_left = mh + np.array([-shoulder_width * 0.1, 0])
        waist_right = mh + np.array([shoulder_width * 0.1, 0])
    
    # More natural hem positioning
    hem_expand = shoulder_width * 0.15
    hem_left = la + np.array([-hem_expand, 0])
    hem_right = ra + np.array([hem_expand, 0])
    hem_center = (hem_left + hem_right) / 2 + np.array([0, shoulder_width * 0.05])
    
    # Create dress polygon with better proportions
    poly = np.stack([
        left_shoulder, right_shoulder,  # Shoulders
        waist_right, waist_left,        # Waist
        hem_right, hem_center, hem_left # Hem
    ], axis=0).astype(np.float32)
    return poly


def _resample_polygon(pts: np.ndarray, n_points: int) -> np.ndarray:
    """Resample a closed polygon (pts Nx2) to have exactly n_points using linear interpolation along the perimeter."""
    if pts is None or len(pts) == 0:
        return pts
    if n_points <= 0:
        return pts
    pts = np.asarray(pts, dtype=np.float32)
    # ensure closed loop
    if not np.allclose(pts[0], pts[-1]):
        closed = np.vstack([pts, pts[0]])
    else:
        closed = pts

    # compute segment lengths
    segs = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    perimeter = np.sum(segs)
    if perimeter == 0 or np.isnan(perimeter):
        # fallback to repeating points
        repeats = np.tile(pts, (int(np.ceil(n_points / len(pts))), 1))[:n_points]
        return repeats.astype(np.float32)

    # sample equally spaced distances along perimeter
    distances = np.linspace(0, perimeter, n_points, endpoint=False)

    # build cumulative lengths
    cum = np.concatenate([[0.0], np.cumsum(segs)])

    res = []
    for d in distances:
        # find segment
        idx = np.searchsorted(cum, d, side='right') - 1
        idx = min(max(idx, 0), len(segs)-1)
        seg_start = closed[idx]
        seg_end = closed[idx+1]
        seg_len = segs[idx]
        if seg_len == 0:
            t = 0.0
        else:
            t = (d - cum[idx]) / seg_len
            t = np.clip(t, 0.0, 1.0)
        point = seg_start + (seg_end - seg_start) * t
        res.append(point)
    return np.array(res, dtype=np.float32)


def get_source_points(cloth_img, n_points: int = None):
    """Return a set of source points (np.ndarray Nx2) for the given cloth image.
    Attempts to extract the main garment contour from the alpha channel. Falls
    back to rectangle corners if extraction fails. If n_points is provided,
    resample the returned polygon to have exactly n_points points.
    """
    try:
        import cv2
        if hasattr(cloth_img, 'convert'):
            img = cloth_img.convert('RGBA')
            arr = np.array(img)
        else:
            arr = np.array(cloth_img)

        # extract alpha channel if present
        if arr.ndim == 3 and arr.shape[2] == 4:
            alpha = arr[:, :, 3]
        else:
            # create mask from non-white/transparent pixels
            if arr.ndim == 3 and arr.shape[2] >= 3:
                gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
                _, alpha = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
            else:
                alpha = np.ones((arr.shape[0], arr.shape[1]), dtype=np.uint8) * 255

        # find contours
        contours, _ = cv2.findContours(alpha.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pts = None
        if contours:
            # pick largest contour
            c = max(contours, key=cv2.contourArea)
            # approximate polygon
            eps = max(1, 0.01 * cv2.arcLength(c, True))
            approx = cv2.approxPolyDP(c, eps, True)
            pts = approx.reshape(-1, 2).astype(np.float32)
            if pts.shape[0] < 4:
                pts = None

        # fallback: use image bbox corners
        if pts is None:
            h, w = arr.shape[0], arr.shape[1]
            pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)

        if n_points and n_points > 0 and pts.shape[0] != n_points:
            pts = _resample_polygon(pts, n_points)

        return pts
    except Exception as e:
        # conservative fallback
        try:
            h, w = getattr(cloth_img, 'size', (100, 200))[1], getattr(cloth_img, 'size', (100, 200))[0]
            pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
            if n_points and n_points > 0 and pts.shape[0] != n_points:
                pts = _resample_polygon(pts, n_points)
            return pts
        except Exception:
            base = np.array([[0, 0], [100, 0], [100, 200], [0, 200]], dtype=np.float32)
            if n_points and n_points > 0 and base.shape[0] != n_points:
                return _resample_polygon(base, n_points)
            return base
