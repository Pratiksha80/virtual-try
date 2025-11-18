import os
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

class ClothFormer:
    def __init__(self, use_gpu=True):
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        print(f"🚀 Using device: {self.device}")
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((512, 384)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        
        # Initialize models (will be loaded when needed)
        self.clothformer = None
        self.parser = None
        self.pose_estimator = None
        
    def load_models(self):
        """Load ClothFormer models if not already loaded"""
        if self.clothformer is None:
            try:
                from .model_downloader import MODEL_PATHS
                
                # Load pre-trained models
                self.clothformer = self._load_model(MODEL_PATHS['clothformer_base.pth'])
                self.parser = self._load_model(MODEL_PATHS['parser.pth'])
                self.pose_estimator = self._load_model(MODEL_PATHS['pose_estimator.pth'])
                
                # Move models to device
                self.clothformer = self.clothformer.to(self.device)
                self.parser = self.parser.to(self.device)
                self.pose_estimator = self.pose_estimator.to(self.device)
                
                print("✅ ClothFormer models loaded successfully")
            except Exception as e:
                print(f"❌ Error loading ClothFormer models: {e}")
                raise
    
    def _load_model(self, path):
        """Helper to load a model with error handling"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model not found at {path}")
            model = torch.load(path, map_location=self.device)
            return model
        except Exception as e:
            raise FileNotFoundError(f"Error loading model from {path}: {str(e)}")

    def process(self, person_img, cloth_img):
        """Process a try-on request using ClothFormer"""
        try:
            # Load models if needed
            self.load_models()
            
            # Preprocess images
            person = self.transform(person_img).unsqueeze(0).to(self.device)
            cloth = self.transform(cloth_img).unsqueeze(0).to(self.device)
            
            # Get pose estimation
            pose = self.pose_estimator(person)
            
            # Get person parsing
            parse = self.parser(person)
            
            # Generate try-on result
            with torch.no_grad():
                output = self.clothformer(
                    person, cloth, pose, parse,
                    return_intermediate=False
                )
            
            # Post-process output
            output = output.squeeze(0).cpu()
            output = (output * 0.5 + 0.5).clamp(0, 1)
            output = transforms.ToPILImage()(output)
            
            return output
            
        except Exception as e:
            print(f"❌ Error in ClothFormer processing: {e}")
            raise