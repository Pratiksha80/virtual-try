#!/usr/bin/env python3
"""
Test script for the virtual try-on system
"""
import os
import sys
import json
import base64
from PIL import Image
import requests

# Add current directory to path
sys.path.append('.')

def test_tryon_with_files():
    """Test the try-on system with local files"""
    print("🧪 Testing Virtual Try-On System")
    print("=" * 50)
    
    # Find sample images
    user_dir = "uploads/user"
    cloth_dir = "uploads/cloth"
    
    # Get first available user image
    user_files = [f for f in os.listdir(user_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    cloth_files = [f for f in os.listdir(cloth_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not user_files or not cloth_files:
        print("❌ No test images found!")
        return
    
    user_img_path = os.path.join(user_dir, user_files[0])
    cloth_img_path = os.path.join(cloth_dir, cloth_files[0])
    
    print(f"👤 User image: {user_img_path}")
    print(f"👕 Cloth image: {cloth_img_path}")
    
    # Test the tryon_process function directly
    try:
        from ai_engine.tryon_processor import tryon_process
        
        print("\n🔄 Running try-on process...")
        result = tryon_process(
            user_img_source=user_img_path,
            cloth_img_source=cloth_img_path,
            cloth_type="shirt"
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"✅ Try-on completed successfully!")
        print(f"📏 Recommended size: {result.get('preferred_size', 'Unknown')}")
        
        # Save the result
        if "output_image_base64" in result:
            image_data = base64.b64decode(result["output_image_base64"])
            output_path = "uploads/debug/test_result.png"
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"💾 Result saved to: {output_path}")
            
            # Show image info
            img = Image.open(output_path)
            print(f"📐 Result image size: {img.size}")
        
    except Exception as e:
        print(f"❌ Error during try-on: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n🌐 Testing API Endpoint")
    print("=" * 30)
    
    # Find sample images
    user_dir = "uploads/user"
    cloth_dir = "uploads/cloth"
    
    user_files = [f for f in os.listdir(user_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    cloth_files = [f for f in os.listdir(cloth_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not user_files or not cloth_files:
        print("❌ No test images found!")
        return
    
    user_img_path = os.path.join(user_dir, user_files[0])
    cloth_img_path = os.path.join(cloth_dir, cloth_files[0])
    
    # Convert images to base64
    with open(user_img_path, "rb") as f:
        user_b64 = base64.b64encode(f.read()).decode()
    
    with open(cloth_img_path, "rb") as f:
        cloth_b64 = base64.b64encode(f.read()).decode()
    
    # Test API call
    try:
        response = requests.post(
            "http://localhost:8000/tryon",
            json={
                "user_image": user_img_path,  # Use file path for testing
                "cloth_image": cloth_img_path,
                "cloth_type": "shirt"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"📏 Recommended size: {result.get('preferred_size', 'Unknown')}")
            
            if "output_image_base64" in result:
                image_data = base64.b64decode(result["output_image_base64"])
                output_path = "uploads/debug/api_test_result.png"
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"💾 API result saved to: {output_path}")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Virtual Try-On Test")
    print("=" * 50)
    
    # Test direct function call
    test_tryon_with_files()
    
    # Test API endpoint
    test_api_endpoint()
    
    print("\n🎉 Test completed!")
    print("Check the 'uploads/debug/' folder for results and debug images.")
