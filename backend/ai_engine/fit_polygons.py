# backend/ai_engine/fit_polygons.py
import numpy as np

def _pt(kps, idx_map, name):
    return kps[idx_map[name]] if name in idx_map else None

def target_poly_shirt(kps: np.ndarray, idx_map: dict) -> np.ndarray:
    ls = _pt(kps, idx_map, "left_shoulder")
    rs = _pt(kps, idx_map, "right_shoulder")
    mh = _pt(kps, idx_map, "mid_hip")
    ms = _pt(kps, idx_map, "mid_shoulder")
    if any(x is None for x in [ls, rs, mh, ms]):
        raise ValueError("missing keypoints for shirt")
    # width slightly beyond shoulders
    expand = 0.10 * np.linalg.norm(rs - ls)
    left_top  = ls + np.array([-expand, 0])
    right_top = rs + np.array([+expand, 0])
    # armpits approx: 1/3 down towards mid-hip
    left_pit  = ls + (mh - ls) * 0.33
    right_pit = rs + (mh - rs) * 0.33
    # bottom hem near mid-hip, with slight curve points
    hem_left  = mh + (ls - ms) * 0.05
    hem_mid   = mh
    hem_right = mh + (rs - ms) * 0.05
    poly = np.stack([left_top, right_top, right_pit, hem_right, hem_mid, hem_left, left_pit], axis=0).astype(np.float32)
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
    if any(x is None for x in [ls,rs,ms,la,ra,mh]):
        raise ValueError("missing keypoints for dress")
    hem_left  = la + (la - mh) * 0.05
    hem_right = ra + (ra - mh) * 0.05
    poly = np.stack([ls, rs, mh, hem_right, (hem_left+hem_right)/2, hem_left], axis=0).astype(np.float32)
    return poly
