# backend/ai_engine/warp_mesh.py
import cv2, numpy as np
from scipy.spatial import Delaunay
from typing import Tuple

def _triangulate(points: np.ndarray) -> np.ndarray:
    tri = Delaunay(points)
    return tri.simplices  # (T,3) indices

def _warp_triangle(src, dst, img_src, img_dst):
    r1 = cv2.boundingRect(np.float32([src]))
    r2 = cv2.boundingRect(np.float32([dst]))

    src_cropped = img_src[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
    src_tri = np.float32([[pt[0]-r1[0], pt[1]-r1[1]] for pt in src])
    dst_tri = np.float32([[pt[0]-r2[0], pt[1]-r2[1]] for pt in dst])

    M = cv2.getAffineTransform(src_tri, dst_tri)
    warped = cv2.warpAffine(src_cropped, M, (r2[2], r2[3]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    mask = np.zeros((r2[3], r2[2], 4), dtype=np.uint8)
    cv2.fillConvexPoly(mask, np.int32(dst_tri), (255,255,255,255))
    img_dst_section = img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]]
    blended = cv2.addWeighted(img_dst_section, 1.0, (warped * (mask[:,:,3:4]/255.0)).astype(np.uint8), 1.0, 0)
    img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = np.where(mask>0, blended, img_dst_section)

def warp_rgba_mesh(src_rgba: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray, out_wh: Tuple[int,int]) -> np.ndarray:
    """
    src_rgba: HxWx4 uint8
    src_pts, dst_pts: Nx2 float32 correspondences (N>=8 recommended)
    out_wh: (W,H) of destination canvas
    """
    W, H = out_wh
    out = np.zeros((H, W, 4), dtype=np.uint8)
    tris = _triangulate(dst_pts)
    for a,b,c in tris:
        _warp_triangle(src_pts[[a,b,c]], dst_pts[[a,b,c]], src_rgba, out)
    return out
