import os
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
import cv2

def to_tensor(img):
    # Convert PIL Image or cv2 ndarray to tensor
    if isinstance(img, Image.Image):
        # PIL Image to numpy
        img = np.array(img)
    
    # Ensure image is RGB
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    
    # Resize to 512x384
    img = cv2.resize(img, (384, 512))
    
    # Convert to float32 and normalize
    img = img.astype(np.float32) / 255.0
    img = (img - 0.5) / 0.5
    
    # Convert to tensor with shape [C, H, W]
    img = img.transpose((2, 0, 1))
    img = torch.from_numpy(img).float()
    
    return img

class VITONHD:
    def __init__(self, use_gpu=True):
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        print(f"🚀 Using device: {self.device}")
        
        # Check models directory exists
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir, exist_ok=True)
            print(f"📁 Created models directory at: {models_dir}")
        
        # Define image preprocessing function
        self.transform = to_tensor
        
        # Initialize models (will be loaded when needed)
        self.clothformer = None
        self.parser = None
        self.pose_estimator = None
        
    def load_models(self):
        """Load ClothFormer models if not already loaded"""
        if self.clothformer is None:
            try:
                from .model_downloader import MODEL_PATHS, verify_model_files
                
                # First verify that all required model files are present
                verify_model_files()
                
                # Load pre-trained models
                print("\n📂 Loading VITON-HD models...")
                self.clothformer = self._load_model(MODEL_PATHS['gen_latest.pth'])  # ACGPN generator
                print("✅ Loaded generator model")
                
                self.parser = self._load_model(MODEL_PATHS['u2net.pth'])  # U2NET segmentation
                print("✅ Loaded segmentation model")
                
                self.pose_estimator = self._load_model(MODEL_PATHS['warp_latest.pth'])  # ACGPN warping
                print("✅ Loaded warping model")
                
                # Move models to device
                print(f"\n🚀 Moving models to device: {self.device}")
                self.clothformer = self.clothformer.to(self.device)
                self.parser = self.parser.to(self.device)
                self.pose_estimator = self.pose_estimator.to(self.device)
                
                print("✅ All ClothFormer models loaded successfully")
            except Exception as e:
                print(f"❌ Error loading ClothFormer models: {e}")
                print("\nMake sure all required model files are present in the correct location:")
                print("  - backend/models/viton/gen_latest.pth")
                print("  - backend/models/viton/u2net.pth")
                print("  - backend/models/viton/warp_latest.pth")
                raise
    
    def _load_model(self, path):
        """Helper to load a model with error handling"""
        try:
            if not os.path.exists(path):
                error_msg = f"""
❌ Required model file not found: {os.path.basename(path)}

Please ensure the following model files are placed in the backend/ai_engine/models directory:
1. clothformer_base.pth
2. parser.pth
3. pose_estimator.pth

These are proprietary model files that need to be obtained from the project maintainer.
"""
                print(error_msg)
                raise FileNotFoundError(error_msg)
            model = torch.load(path, map_location=self.device, weights_only=False)
            model.eval()
            return model
        except Exception as e:
            print(f"❌ Error loading model from {path}: {e}")
            raise

    def preprocess_image(self, image):
        """Preprocess image for VITON-HD"""
        if isinstance(image, str):
            image = Image.open(image)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return self.transform(image).unsqueeze(0).to(self.device)

    def process(self, person_image, cloth_image):
        """
        Process virtual try-on with VITON-HD
        Args:
            person_image: Path or PIL Image of person
            cloth_image: Path or PIL Image of clothing
        Returns:
            PIL Image of try-on result
        """
        try:
            self.load_models()
            
            # Preprocess images
            person_tensor = self.preprocess_image(person_image)
            cloth_tensor = self.preprocess_image(cloth_image)
            
            # Get person segmentation
            with torch.no_grad():
                seg_out = self.segmentation_model(person_tensor)
                
            # Warp clothing
            warp_out = self.warp_model(cloth_tensor, seg_out)
            
            # Generate final try-on
            gen_input = torch.cat([person_tensor, warp_out], dim=1)
            gen_out = self.gen_model(gen_input)
            
            # Convert to image
            result = gen_out.squeeze(0).cpu()
            result = (result * 0.5 + 0.5).clamp(0, 1).numpy()
            
            # Convert from [C,H,W] to [H,W,C]
            result = result.transpose(1, 2, 0)
            
            # Convert to uint8
            result = (result * 255).astype('uint8')
            
            # Convert to PIL Image
            result = Image.fromarray(result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error in VITON-HD processing: {e}")
            import traceback
            traceback.print_exc()
            raise

# Initialize as singleton
viton_model = None

def get_viton_model():
    global viton_model
    if viton_model is None:
        viton_model = VITONHD()
    return viton_model