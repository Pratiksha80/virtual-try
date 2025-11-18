import os
import cv2
from person_pose import infer_keypoints

def test_pose_detection():
    # Create a test directory in uploads if it doesn't exist
    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "test")
    os.makedirs(test_dir, exist_ok=True)

    # Create a simple test image with a person
    img_path = os.path.join(test_dir, "test_pose.jpg")
    
    try:
        # Try to detect pose
        result = infer_keypoints(img_path)
        
        # Print detected keypoints
        print("\n✅ Pose detection is working!")
        print(f"Found {len(result['kps'])} keypoints")
        print("\nDetected joints:")
        for name, idx in result['index_map'].items():
            x, y = result['kps'][idx]
            conf = result['conf'][idx]
            print(f"{name:15s}: x={x:6.1f}, y={y:6.1f}, confidence={conf:.2f}")
        
        return True
    except Exception as e:
        print(f"\n❌ Pose detection test failed: {e}")
        return False

if __name__ == "__main__":
    test_pose_detection()