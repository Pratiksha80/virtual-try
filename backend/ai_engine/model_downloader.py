# backend/ai_engine/model_downloader.py
import os
import requests

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
VITON_DIR = os.path.join(MODEL_DIR, "viton")

from huggingface_hub import hf_hub_download

# Model paths - Using ACGPN models and pose estimation
MODEL_FILES = {
    "gen_latest.pth": {
        "url": None,  # Local file only
        "filename": "gen_latest.pth",
        "required": True,
        "description": "VITON-HD Generator model"
    },
    "u2net.pth": {
        "url": None,  # Local file only
        "filename": "u2net.pth",
        "required": True,
        "description": "U2NET Segmentation model"
    },
    "warp_latest.pth": {
        "url": None,  # Local file only
        "filename": "warp_latest.pth",
        "required": True,
        "description": "VITON-HD Warping model"
    },
    # Using MediaPipe pose estimation instead of OpenPose
    "mediapipe_pose": {
        "url": None,  # MediaPipe downloads models automatically
        "filename": None,
        "required": False,
        "description": "MediaPipe Pose model (auto-downloaded)"
    }
}

# Local paths
MODEL_PATHS = {
    name: os.path.join(MODEL_DIR if name == 'body_25.onnx' else VITON_DIR, name)
    for name, info in MODEL_FILES.items()
    if info["filename"] is not None  # Only include files with filenames
}

def verify_model_files():
    """Verify that all required model files are present in the correct locations"""
    missing_models = []
    found_models = []

    # Create directories if they don't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(VITON_DIR, exist_ok=True)
    
    for name, info in MODEL_FILES.items():
        if not info["required"] or info["filename"] is None:
            continue
            
        model_path = MODEL_PATHS[name]
        if not os.path.exists(model_path):
            missing_models.append((name, info["description"]))
        else:
            found_models.append((name, info["description"]))
            
    # Report status
    if found_models:
        print("\n✅ Found model files:")
        for name, desc in found_models:
            print(f"  - {name}: {desc}")
            
    if missing_models:
        print("\n❌ Missing required model files:")
        for name, desc in missing_models:
            print(f"  - {name}: {desc}")
        raise RuntimeError("Missing required model files. Please ensure all model files are in the correct location.")
    else:
        print("\n✅ All required model files are present")
    
    return True

def download_file(url: str, path: str):
    print(f"📥 Downloading {os.path.basename(path)}...")
    
    # Start session for handling Google Drive downloads
    session = requests.Session()
    response = session.get(url, stream=True)
    response.raise_for_status()
    
    # Handle Google Drive download confirmation
    if "drive.google.com" in url:
        try:
            # Get the confirmation token
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    url = url + '&confirm=' + value
                    response = session.get(url, stream=True)
                    break
        except Exception as e:
            print(f"Warning: Could not handle Google Drive confirmation: {e}")
    
    # Download the file
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def download_from_url(url, local_path, session):
    """Download file from direct URL with progress tracking"""
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        written = 0
        
        print(f"💾 Downloading file ({total_size/1024/1024:.1f} MB)")
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
                    if total_size > 0:
                        percent = (written / total_size) * 100
                        print(f"\r📥 Progress: {percent:.1f}% ({written/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB)", end="")
        
        print("\n✅ Download complete!")
        return True
    except Exception as e:
        print(f"\n⚠️ Direct download failed: {e}")
        if "404" in str(e):
            print("❌ File not found at URL")
        elif "403" in str(e):
            print("❌ Access denied to file")
        return False

def ensure_model():
    """Ensure all required model files are available"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"📁 Using models directory: {MODEL_DIR}")

    # Create viton subdirectory
    viton_dir = os.path.join(MODEL_DIR, "viton")
    os.makedirs(viton_dir, exist_ok=True)

    # Set up authentication token
    # Set up session with download headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    success = True

    for model_file, info in MODEL_FILES.items():
        if info["filename"] is None:
            continue
            
        local_path = os.path.join(viton_dir, os.path.basename(info["filename"]))
        if os.path.exists(local_path):
            print(f"✅ {model_file} already exists at {local_path}")
            continue

        print(f"📥 Downloading {model_file}...")
        
        # Try direct URL download first
        if "url" in info:
            if download_from_url(info["url"], local_path, session):
                print(f"✅ Downloaded {model_file} from direct URL")
                continue
                    
        # Try Hugging Face download
        try:
            print(f"⚠️ Trying Hugging Face download...")
            downloaded_path = hf_hub_download(
                repo_id=info["repo_id"],
                filename=info["filename"],
                subfolder=info.get("subfolder"),
                local_dir=viton_dir,
                local_dir_use_symlinks=False
            )
            print(f"✅ Downloaded {model_file} from Hugging Face to {downloaded_path}")
            continue
        except Exception as e:
            print(f"⚠️ Hugging Face download failed: {e}")
            
        # If all download attempts failed
        print(f"❌ Failed to download {model_file}")
        print(f"Please manually place the file at: {local_path}")
        success = False

    if not success:
        raise RuntimeError("""
❌ Failed to download one or more model files. Please either:

1. Place the model files manually in:
   {}/viton/
   Required files:
   - clothformer_base.pth
   - parser.pth
   - pose_estimator.pth

2. Or use Hugging Face authentication:
   Run: huggingface-cli login
   And enter your access token when prompted
""".format(MODEL_DIR))

    print("✅ All models verified")
    return MODEL_PATHS

if __name__ == "__main__":
    ensure_model()
