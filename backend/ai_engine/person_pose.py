# backend/ai_engine/person_pose.py
import cv2, numpy as np
from typing import Dict, Any
import mediapipe as mp

_mp_holistic = None

def _load_holistic():
    global _mp_holistic
    if _mp_holistic is None:
        _mp_holistic = mp.solutions.holistic.Holistic(
            static_image_mode=True, model_complexity=1, enable_segmentation=False
        )
    return _mp_holistic

def infer_keypoints(img_path: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "kps": np.ndarray (N,2)  in pixel coords (N >= 75),
        "conf": np.ndarray (N,),
        "index_map": dict  # name -> index for common joints
      }
    """
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        raise RuntimeError(f"cannot read image: {img_path}")
    h, w = img_bgr.shape[:2]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    holistic = _load_holistic()
    res = holistic.process(img_rgb)

    kps = []
    conf = []
    index_map = {}

    def _add_landmarks(landmarks, prefix):
        start = len(kps)
        if landmarks:
            for lm in landmarks.landmark:
                kps.append([lm.x * w, lm.y * h])
                conf.append(lm.visibility if hasattr(lm, "visibility") else 1.0)
        # build index map only for known pose joints we'll use
        if prefix == "pose" and landmarks:
            names = {
                "nose":0, "left_eye_inner":1, "left_eye":2, "left_eye_outer":3,
                "right_eye_inner":4, "right_eye":5, "right_eye_outer":6,
                "left_ear":7, "right_ear":8,
                "left_shoulder":11, "right_shoulder":12,
                "left_elbow":13, "right_elbow":14,
                "left_wrist":15, "right_wrist":16,
                "left_hip":23, "right_hip":24,
                "left_knee":25, "right_knee":26,
                "left_ankle":27, "right_ankle":28,
                "left_heel":29, "right_heel":30,
                "left_foot_index":31, "right_foot_index":32
            }
            for name, pid in names.items():
                index_map[name] = start + pid

    _add_landmarks(res.pose_landmarks, "pose")
    _add_landmarks(res.left_hand_landmarks, "lh")
    _add_landmarks(res.right_hand_landmarks, "rh")

    kps = np.array(kps, dtype=np.float32) if kps else np.zeros((0,2), np.float32)
    conf = np.array(conf, dtype=np.float32) if conf else np.zeros((0,), np.float32)

    # derive a few centers we'll use
    def _mid(a, b):
        nonlocal kps
        if a in index_map and b in index_map:
            idx = len(kps)
            pa = kps[index_map[a]]
            pb = kps[index_map[b]]
            kps_list = kps.tolist()
            kps_list.append(((pa + pb) / 2.0).tolist())
            kps = np.array(kps_list, dtype=np.float32)
            return kps, idx
        return kps, None

    # add mid-shoulder & mid-hip
    kps, mid_shoulder_idx = _mid("left_shoulder", "right_shoulder")
    if mid_shoulder_idx is not None:
        index_map["mid_shoulder"] = mid_shoulder_idx
        conf = np.append(conf, [1.0])

    kps, mid_hip_idx = _mid("left_hip", "right_hip")
    if mid_hip_idx is not None:
        index_map["mid_hip"] = mid_hip_idx
        conf = np.append(conf, [1.0])

    # Validate and estimate essential keypoints for clothing fitting
    essential_keypoints = ["left_shoulder", "right_shoulder", "mid_shoulder", "mid_hip", "left_hip", "right_hip"]
    missing_keypoints = [kp for kp in essential_keypoints if kp not in index_map]
    
    if missing_keypoints:
        print(f"⚠️ Warning: Missing essential keypoints: {missing_keypoints}")
        # Try to estimate missing keypoints if possible
        
        # Estimate shoulders if missing
        if "left_shoulder" not in index_map and "right_shoulder" in index_map:
            # Estimate left shoulder based on right shoulder and neck
            right_shoulder = kps[index_map["right_shoulder"]]
            idx = len(kps)
            estimated_left = right_shoulder + [-0.2 * w, 0]  # Estimate 20% of image width to the left
            kps = np.append(kps, [estimated_left], axis=0)
            conf = np.append(conf, [0.5])  # Lower confidence for estimated point
            index_map["left_shoulder"] = idx
            
        if "right_shoulder" not in index_map and "left_shoulder" in index_map:
            # Estimate right shoulder based on left shoulder
            left_shoulder = kps[index_map["left_shoulder"]]
            idx = len(kps)
            estimated_right = left_shoulder + [0.2 * w, 0]
            kps = np.append(kps, [estimated_right], axis=0)
            conf = np.append(conf, [0.5])
            index_map["right_shoulder"] = idx
            
        # Estimate mid points
        if "mid_shoulder" not in index_map and "left_shoulder" in index_map and "right_shoulder" in index_map:
            # Add mid_shoulder if we have both shoulders
            idx = len(kps)
            ls = kps[index_map["left_shoulder"]]
            rs = kps[index_map["right_shoulder"]]
            kps_list = kps.tolist()
            kps_list.append(((ls + rs) / 2.0).tolist())
            kps = np.array(kps_list, dtype=np.float32)
            index_map["mid_shoulder"] = idx
            conf = np.append(conf, [1.0])
        
        if "mid_hip" not in index_map and "left_hip" in index_map and "right_hip" in index_map:
            # Add mid_hip if we have both hips
            idx = len(kps)
            lh = kps[index_map["left_hip"]]
            rh = kps[index_map["right_hip"]]
            kps_list = kps.tolist()
            kps_list.append(((lh + rh) / 2.0).tolist())
            kps = np.array(kps_list, dtype=np.float32)
            index_map["mid_hip"] = idx
            conf = np.append(conf, [1.0])

    # Check confidence scores and warn about low-confidence detections
    low_confidence_keypoints = []
    for name, idx in index_map.items():
        if idx < len(conf) and conf[idx] < 0.5:
            low_confidence_keypoints.append(name)
    
    if low_confidence_keypoints:
        print(f"⚠️ Warning: Low confidence keypoints detected: {low_confidence_keypoints}")

    return {"kps": kps, "conf": conf, "index_map": index_map, "size": (w, h)}
