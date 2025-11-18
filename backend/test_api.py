#!/usr/bin/env python3
"""
Test the API endpoint
"""
import requests
import json

def test_api():
    print('🌐 Testing API Endpoint')
    print('=' * 30)

    try:
        # Test the health endpoint
        response = requests.get('http://localhost:8000/')
        print(f'✅ Health check: {response.status_code}')
        print(f'Response: {response.json()}')
        
        # Test the try-on endpoint
        test_data = {
            'user_image': 'uploads/user/00a7d6a37078481681dfd470aec04ea1_WIN_20250510_09_33_23_Pro.jpg',
            'cloth_image': 'uploads/cloth/cloth_008a771b9e2b43198aa18b3f1acad278.png',
            'cloth_type': 'shirt'
        }
        
        print('\n🔄 Testing try-on API...')
        response = requests.post('http://localhost:8000/tryon', json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print('✅ API call successful!')
            print(f'📏 Recommended size: {result.get("preferred_size", "Unknown")}')
            print(f'📊 Response size: {len(str(result))} characters')
        else:
            print(f'❌ API call failed: {response.status_code}')
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    test_api()
