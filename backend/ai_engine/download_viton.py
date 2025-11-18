import os
import requests
from tqdm import tqdm

VITON_HD_MODELS = {
    'segmentation.pth': 'https://github.com/levindabhi/ACGPN/releases/download/v1.0.0/u2net.pth',
    'warp.pth': 'https://github.com/levindabhi/ACGPN/releases/download/v1.0.0/warp_latest.pth',
    'gen.pth': 'https://github.com/levindabhi/ACGPN/releases/download/v1.0.0/gen_latest.pth'
}

def download_viton_models():
    """Download VITON-HD model weights if not already present"""
    models_dir = os.path.join(os.path.dirname(__file__), 'models', 'viton')
    os.makedirs(models_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for model_name, url in VITON_HD_MODELS.items():
        model_path = os.path.join(models_dir, model_name)
        
        if not os.path.exists(model_path):
            print(f"⬇️ Downloading {model_name}...")
            try:
                session = requests.Session()
                response = session.get(url, headers=headers, stream=True, allow_redirects=True)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('application/octet-stream'):
                    raise ValueError(f"Invalid content type: {content_type}")
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(model_path, 'wb') as f, tqdm(
                    desc=model_name,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for data in response.iter_content(chunk_size=1024):
                        size = f.write(data)
                        pbar.update(size)
                        
                print(f"✅ Successfully downloaded {model_name}")
            except Exception as e:
                print(f"❌ Error downloading {model_name}: {e}")
                if os.path.exists(model_path):
                    os.remove(model_path)
        else:
            print(f"✓ {model_name} already exists")

if __name__ == '__main__':
    download_viton_models()