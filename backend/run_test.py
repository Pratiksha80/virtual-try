#!/usr/bin/env python3
"""
Complete test of the virtual try-on system
"""
import os
import base64
from ai_engine.tryon_processor import tryon_process

def main():
    print('🚀 Running Complete Virtual Try-On Test')
    print('=' * 50)

    # Get sample images
    user_files = [f for f in os.listdir('uploads/user') if f.endswith(('.jpg', '.png'))]
    cloth_files = [f for f in os.listdir('uploads/cloth') if f.endswith(('.jpg', '.png'))]

    if not user_files or not cloth_files:
        print('❌ No test images found')
        return

    user_img = f'uploads/user/{user_files[0]}'
    cloth_img = f'uploads/cloth/{cloth_files[0]}'
    
    print(f'👤 User: {user_img}')
    print(f'👕 Cloth: {cloth_img}')
    print()
    
    try:
        print('🔄 Processing virtual try-on...')
        result = tryon_process(user_img, cloth_img, 'shirt')
        
        if 'error' in result:
            print(f'❌ Error: {result["error"]}')
        else:
            print('✅ Virtual try-on completed successfully!')
            print(f'📏 Recommended size: {result.get("preferred_size", "Unknown")}')
            
            # Save result
            if 'output_image_base64' in result:
                img_data = base64.b64decode(result['output_image_base64'])
                output_path = 'uploads/debug/complete_test_result.png'
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                print(f'💾 Result saved to: {output_path}')
                
                # Show file size
                file_size = os.path.getsize(output_path) / 1024
                print(f'📊 File size: {file_size:.1f} KB')
                
    except Exception as e:
        print(f'❌ Error during processing: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
