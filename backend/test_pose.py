import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
import os

def infer_keypoints(img_path: str) -> dict:
    """
    Reimplementation of the core functionality from person_pose.py
    without dependencies on other modules
    """
    mp_holistic = mp.solutions.holistic.Holistic(
        static_image_mode=True, model_complexity=1, enable_segmentation=False
    )

    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        raise RuntimeError(f"cannot read image: {img_path}")
    h, w = img_bgr.shape[:2]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    res = mp_holistic.process(img_rgb)

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

    mp_holistic.close()
    return {"kps": kps, "conf": conf, "index_map": index_map}

def test_pose_detection():
    # Find an image file in the user uploads directory
    user_dir = r"d:\Virtual-Try\backend\uploads\user"
    test_image = None
    for filename in os.listdir(user_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            test_image = os.path.join(user_dir, filename)
            break

    if test_image is None:
        print("❌ Error: Could not find any image files in the uploads directory")
        return

    print(f"Testing with image: {test_image}")
    
    # Call our pose detection
    try:
        result = infer_keypoints(test_image)
        print("✅ Successfully detected pose")
        print(f"Number of keypoints detected: {len(result['kps'])}")
        print("\nDetected joints with coordinates:")
        for joint_name, idx in result['index_map'].items():
            x, y = result['kps'][idx]
            conf = result['conf'][idx]
            print(f"{joint_name:15s}: ({x:.1f}, {y:.1f}) confidence: {conf:.2f}")

        # Visualize the results
        img = cv2.imread(test_image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        plt.figure(figsize=(12, 8))
        plt.imshow(img)
        
        # Plot keypoints
        for joint_name, idx in result['index_map'].items():
            x, y = result['kps'][idx]
            conf = result['conf'][idx]
            if conf > 0.5:  # Only show high confidence points
                plt.plot(x, y, 'o', label=joint_name)
        
        # Connect body parts
        body_connections = [
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_elbow"),
            ("left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow"),
            ("right_elbow", "right_wrist"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
            ("left_hip", "left_knee"),
            ("left_knee", "left_ankle"),
            ("right_hip", "right_knee"),
            ("right_knee", "right_ankle")
        ]
        
        for start, end in body_connections:
            if start in result['index_map'] and end in result['index_map']:
                start_idx = result['index_map'][start]
                end_idx = result['index_map'][end]
                if result['conf'][start_idx] > 0.5 and result['conf'][end_idx] > 0.5:
                    plt.plot([result['kps'][start_idx][0], result['kps'][end_idx][0]], 
                            [result['kps'][start_idx][1], result['kps'][end_idx][1]], '-')

        plt.title('Pose Detection Results')
        plt.axis('off')
        
        # Save the visualization
        plt.savefig('pose_detection_test.png')
        print("\n✅ Saved visualization to pose_detection_test.png")
        
    except Exception as e:
        print(f"❌ Error during pose detection: {str(e)}")
        raise

if __name__ == "__main__":
    test_pose_detection()