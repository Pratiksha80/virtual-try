import cv2
import mediapipe as mp
import matplotlib.pyplot as plt
import os

def test_basic_pose():
    # Initialize MediaPipe Pose
    mp_holistic = mp.solutions.holistic
    mp_drawing = mp.solutions.drawing_utils

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

    # Initialize holistic model
    with mp_holistic.Holistic(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False
    ) as holistic:
        
        # Read image
        image = cv2.imread(test_image)
        if image is None:
            print(f"❌ Error: Could not read image from {test_image}")
            return
        
        print("✅ Successfully loaded image")
        
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        results = holistic.process(image_rgb)
        
        if results.pose_landmarks:
            print("✅ Successfully detected pose landmarks")
            
            # Create figure for visualization
            fig = plt.figure(figsize=(12, 8))
            plt.imshow(image_rgb)
            
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                image_rgb, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )
            
            plt.title('Basic Pose Detection Results')
            plt.axis('off')
            
            # Save visualization
            plt.savefig('basic_pose_test.png')
            print("✅ Saved visualization to basic_pose_test.png")
            
            # Print the first few landmark coordinates
            print("\nSample landmark coordinates:")
            for idx, landmark in enumerate(results.pose_landmarks.landmark[:5]):
                print(f"Landmark {idx}: x={landmark.x:.3f}, y={landmark.y:.3f}, z={landmark.z:.3f}, visibility={landmark.visibility:.3f}")
        else:
            print("❌ No pose landmarks detected!")

if __name__ == "__main__":
    test_basic_pose()