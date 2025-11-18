import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PIL import Image
from ai_engine.viton_hd import get_viton_model
from ai_engine.download_viton import download_viton_models

def test_viton():
    """Test VITON-HD integration"""
    try:
        # Download models if needed
        print("Downloading models...")
        download_viton_models()
        
        # Initialize VITON-HD
        print("Initializing VITON-HD...")
        model = get_viton_model()
        
        # Load test images
        test_dir = os.path.join(os.path.dirname(__file__), "test_images")
        os.makedirs(test_dir, exist_ok=True)
        
        person_path = os.path.join(test_dir, "person.png")
        cloth_path = os.path.join(test_dir, "cloth.png")
        
        if not os.path.exists(person_path) or not os.path.exists(cloth_path):
            print("Please place test images in test_images/:")
            print("- person.png: A front-facing person image")
            print("- cloth.png: A front-facing clothing image")
            return
        
        # Run inference
        print("Running VITON-HD inference...")
        person_img = Image.open(person_path)
        cloth_img = Image.open(cloth_path)
        
        result = model.process(person_img, cloth_img)
        
        # Save result
        result_path = os.path.join(test_dir, "viton_result.png")
        result.save(result_path)
        print(f"✅ Test successful! Result saved to {result_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_viton()