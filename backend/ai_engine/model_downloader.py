# backend/ai_engine/model_downloader.py
import os
import requests

MODEL_DIR = os.path.join("ai_engine", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "cloth_segmentation.onnx")
MODEL_URL = "https://huggingface.co/akhaliq/cloth-segmentation/resolve/main/cloth_segm.onnx"

def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print(f"📥 Downloading cloth segmentation model from {MODEL_URL}...")
        response = requests.get(MODEL_URL, stream=True)
        response.raise_for_status()
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"✅ Model saved to {MODEL_PATH}")
    else:
        print(f"✅ Model already exists: {MODEL_PATH}")

if __name__ == "__main__":
    ensure_model()
