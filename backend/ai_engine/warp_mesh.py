# backend/ai_engine/warp_mesh.py
import cv2, numpy as np
from scipy.spatial import Delaunay
from typing import Tuple
import warnings

def _triangulate(points: np.ndarray) -> np.ndarray:
    tri = Delaunay(points)
    return tri.simplices  # (T,3) indices


def _resample_polygon(pts: np.ndarray, n_points: int) -> np.ndarray:
    """Resample a polygon/polyline to exactly n_points along its perimeter.
    Returns an (n_points,2) float32 array.
    """
    pts = np.asarray(pts, dtype=np.float32)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("pts must be an Nx2 array")
    m = pts.shape[0]
    if m == 0:
        return np.zeros((n_points, 2), dtype=np.float32)
    if m == 1:
        return np.tile(pts[0], (n_points, 1)).astype(np.float32)
    if m == n_points:
        return pts.astype(np.float32)

    # compute segment lengths (including closing segment to first point)
    diffs = np.diff(pts, axis=0, append=pts[:1])
    seg_lengths = np.sqrt((diffs ** 2).sum(axis=1))
    total = seg_lengths.sum()
    if total <= 0:
        return np.tile(pts[0], (n_points, 1)).astype(np.float32)

    cum = np.cumsum(seg_lengths)
    # sample n_points evenly spaced distances along the perimeter
    samples = np.linspace(0, total, num=n_points, endpoint=False)
    resampled = []
    seg_idx = 0
    prev_cum = 0.0
    for s in samples:
        # advance seg_idx until s <= cum[seg_idx]
        while seg_idx < len(cum) and cum[seg_idx] < s:
            seg_idx += 1
        if seg_idx >= len(cum):
            seg_idx = len(cum) - 1
        seg_end_idx = (seg_idx + 1) % m
        seg_start = pts[seg_idx]
        seg_end = pts[seg_end_idx]
        seg_len = seg_lengths[seg_idx]
        seg_cum_start = cum[seg_idx] - seg_len
        if seg_len == 0:
            resampled.append(seg_start)
        else:
            frac = (s - seg_cum_start) / seg_len
            frac = float(np.clip(frac, 0.0, 1.0))
            p = seg_start + frac * (seg_end - seg_start)
            resampled.append(p)

    return np.asarray(resampled, dtype=np.float32)

def _warp_triangle(src, dst, img_src, img_dst):
    r1 = cv2.boundingRect(np.float32([src]))
    r2 = cv2.boundingRect(np.float32([dst]))

    # Increase padding for better edge handling
    padding = 5  # Increased padding
    r1_padded = (max(0, r1[0] - padding), max(0, r1[1] - padding), 
                 min(img_src.shape[1] - r1[0], r1[2] + 2*padding),
                 min(img_src.shape[0] - r1[1], r1[3] + 2*padding))
    r2_padded = (max(0, r2[0] - padding), max(0, r2[1] - padding), 
                 min(img_dst.shape[1] - r2[0], r2[2] + 2*padding),
                 min(img_dst.shape[0] - r2[1], r2[3] + 2*padding))

    src_cropped = img_src[r1_padded[1]:r1_padded[1]+r1_padded[3], r1_padded[0]:r1_padded[0]+r1_padded[2]]
    src_tri = np.float32([[pt[0]-r1_padded[0], pt[1]-r1_padded[1]] for pt in src])
    dst_tri = np.float32([[pt[0]-r2_padded[0], pt[1]-r2_padded[1]] for pt in dst])

    # Use higher quality interpolation
    M = cv2.getAffineTransform(src_tri, dst_tri)
    warped = cv2.warpAffine(src_cropped, M, (r2_padded[2], r2_padded[3]), 
                           flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)

    # Create mask with soft edges for better blending
    mask = np.zeros((r2_padded[3], r2_padded[2], 4), dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.int32(dst_tri), (255,255,255,255))
    
    # Apply stronger Gaussian blur for smoother edges
    mask_blurred = cv2.GaussianBlur(mask, (5, 5), 2)  # Increased blur size and sigma
    
    # Create a larger feathered edge
    kernel = np.ones((3,3), np.uint8)
    mask_dilated = cv2.dilate(mask_blurred, kernel, iterations=2)
    mask_blurred = cv2.GaussianBlur(mask_dilated, (5, 5), 2)
    
    # Ensure we don't go out of bounds
    y_start, y_end = r2_padded[1], min(r2_padded[1] + r2_padded[3], img_dst.shape[0])
    x_start, x_end = r2_padded[0], min(r2_padded[0] + r2_padded[2], img_dst.shape[1])
    
    if y_end > y_start and x_end > x_start:
        img_dst_section = img_dst[y_start:y_end, x_start:x_end]
        warped_section = warped[:y_end-y_start, :x_end-x_start]
        mask_section = mask_blurred[:y_end-y_start, :x_end-x_start]
        
        # Better blending with alpha channel
        alpha = mask_section[:,:,3:4] / 255.0
        blended = img_dst_section * (1 - alpha) + warped_section * alpha
        img_dst[y_start:y_end, x_start:x_end] = blended.astype(np.uint8)

def warp_rgba_mesh(src_rgba: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray, out_wh: Tuple[int,int]) -> np.ndarray:
    """
    src_rgba: HxWx4 uint8
    src_pts, dst_pts: Nx2 float32 correspondences (N>=8 recommended)
    out_wh: (W,H) of destination canvas
    """
    W, H = out_wh
    out = np.zeros((H, W, 4), dtype=np.uint8)

    # ensure inputs are numpy arrays of correct dtype
    src_pts = np.asarray(src_pts, dtype=np.float32)
    dst_pts = np.asarray(dst_pts, dtype=np.float32)

    # If point counts differ, resample source points to match destination length.
    if src_pts.shape[0] != dst_pts.shape[0]:
        try:
            src_pts = _resample_polygon(src_pts, dst_pts.shape[0])
        except Exception as e:
            warnings.warn(f"Failed to resample source polygon: {e}")

    # triangulate destination polygon
    try:
        tris = _triangulate(dst_pts)
    except Exception as e:
        warnings.warn(f"Triangulation failed: {e}; returning blank canvas")
        return out

    # Warp each triangle; guard against invalid triangle indices	
    for tri in tris:
        if len(tri) != 3:
            continue
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        if max(a, b, c) >= src_pts.shape[0] or max(a, b, c) >= dst_pts.shape[0]:
            # skip triangles that reference out-of-bounds indices
            warnings.warn(f"Skipping triangle with out-of-bounds indices: {(a,b,c)}")
            continue
        _warp_triangle(src_pts[[a,b,c]], dst_pts[[a,b,c]], src_rgba, out)
    return out
