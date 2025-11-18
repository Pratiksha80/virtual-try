from ai_engine.viton_hd import VITONHD
from ai_engine.model_downloader import verify_model_files

def test_viton_initialization():
    print("🔍 Testing VITON-HD initialization...")
    
    # First verify model files
    print("\n1️⃣ Verifying model files...")
    try:
        verify_model_files()
    except Exception as e:
        print(f"❌ Model verification failed: {str(e)}")
        return False
        
    # Initialize VITON-HD
    print("\n2️⃣ Initializing VITON-HD...")
    try:
        viton = VITONHD(use_gpu=False)  # Use CPU for testing
        print("✅ VITON-HD instance created")
    except Exception as e:
        print(f"❌ VITON-HD initialization failed: {str(e)}")
        return False
    
    # Try loading models
    print("\n3️⃣ Loading models...")
    try:
        viton.load_models()
        print("✅ Models loaded successfully")
    except Exception as e:
        print(f"❌ Model loading failed: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    success = test_viton_initialization()
    if success:
        print("\n🎉 VITON-HD initialized and ready to use!")
    else:
        print("\n❌ VITON-HD initialization failed. Please check the errors above.")