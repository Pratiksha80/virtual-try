import cv2
import numpy as np
import mediapipe as mp

class ClothSegmentation:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        )
    
    def segment_clothing(self, image_path: str) -> tuple:
        """
        Segments the clothing region using MediaPipe Pose.
        
        Returns:
            tuple: (clothing_mask, upper_body_bbox)
        """
        # Read and process image
        img = cv2.imread(image_path)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # Process image with MediaPipe Pose
        results_pose = self.pose.process(rgb)
        
        if not results_pose.pose_landmarks:
            print("⚠️ No pose landmarks detected")
            return None, None
        
        # Get person segmentation mask
        mask = results_pose.segmentation_mask
        if mask is None:
            print("⚠️ No segmentation mask available")
            return None, None
        
        # Convert mask to binary
        person_mask = (mask > 0.5).astype(np.uint8) * 255
            
        # Extract upper body landmarks for clothing region
        landmarks = results_pose.pose_landmarks.landmark
        
        # Get upper body bounding box
        upper_body_points = []
        for idx in [11, 12, 23, 24]:  # shoulders and hips
            point = landmarks[idx]
            x, y = int(point.x * w), int(point.y * h)
            upper_body_points.append((x, y))
            
        # Calculate bounding box
        upper_body_points = np.array(upper_body_points)
        x_min, y_min = np.min(upper_body_points, axis=0)
        x_max, y_max = np.max(upper_body_points, axis=0)
        
        # Add padding
        padding = int(0.1 * (x_max - x_min))  # 10% padding
        x_min = max(0, x_min - padding)
        x_max = min(w, x_max + padding)
        y_min = max(0, y_min - padding)
        y_max = min(h, y_max + padding)
        
        upper_body_bbox = (x_min, y_min, x_max, y_max)
        
        # Refine clothing mask using pose information
        clothing_mask = person_mask.copy()
        clothing_mask[:y_min, :] = 0  # Remove above upper body
        clothing_mask[y_max:, :] = 0  # Remove below upper body
        
        return clothing_mask, upper_body_bbox

    def remove_existing_clothing(self, image: np.ndarray, clothing_mask: np.ndarray) -> np.ndarray:
        """
        Removes the existing clothing from the image using the clothing mask.
        Uses inpainting to fill the removed region naturally.
        """
        # Create a copy of the image
        result = image.copy()
        
        # Dilate the mask slightly to ensure complete removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        dilated_mask = cv2.dilate(clothing_mask, kernel, iterations=2)
        
        # Inpaint the clothing region
        result = cv2.inpaint(result, dilated_mask, 3, cv2.INPAINT_TELEA)
        
        return result