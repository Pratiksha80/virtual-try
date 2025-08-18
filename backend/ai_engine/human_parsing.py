# backend/ai_engine/human_parsing.py
import cv2, numpy as np
import mediapipe as mp

_selfie = None

def _load_seg():
    global _selfie
    if _selfie is None:
        _selfie = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    return _selfie

def infer_person_mask(img_path: str, thresh: float = 0.5) -> np.ndarray:
    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError(f"cannot read image: {img_path}")
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    seg = _load_seg().process(rgb)
    m = (seg.segmentation_mask >= thresh).astype(np.uint8) * 255
    # clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, 2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN,  kernel, 1)
    return m  # HxW uint8 (0/255)
