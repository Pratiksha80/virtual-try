# backend/routes/tryon.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os, shutil, base64, uuid

try:
    from ai_engine.capture_image import capture_cloth_image
    print("✅ capture_cloth_image loaded.")
except Exception as e:
    capture_cloth_image = None
    print("❌ Error loading capture_cloth_image:", repr(e))

try:
    from ai_engine.tryon_processor import tryon_process
    print("✅ tryon_processor loaded.")
except Exception as e:
    tryon_process = None
    print("❌ Error loading tryon_processor:", repr(e))

router = APIRouter()

@router.post("/tryon/link")
async def tryon_link(
    link: str = Form(...),
    cloth_type: str = Form(...),
    image: UploadFile = File(...)
):
    """Perform try-on from product link + user image (JSON, no SSE)."""
    try:
        # Save user image
        user_dir = os.path.join("uploads", "user")
        os.makedirs(user_dir, exist_ok=True)
        user_filename = f"{uuid.uuid4().hex}_{image.filename}"
        user_img_path = os.path.join(user_dir, user_filename)

        with open(user_img_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

        # Capture cloth image
        cloth_dir = os.path.join("uploads", "cloth")
        os.makedirs(cloth_dir, exist_ok=True)
        cloth_filename = f"cloth_{uuid.uuid4().hex}.png"
        cloth_path = os.path.join(cloth_dir, cloth_filename)

        if not capture_cloth_image:
            raise HTTPException(status_code=500, detail="capture_cloth_image function not found")

        capture_cloth_image(link, cloth_path)

        # Run try-on
        if not tryon_process:
            raise HTTPException(status_code=500, detail="tryon_process function not available")

        result = tryon_process(user_img_path, cloth_path, cloth_type)

        return {"status": "done", "output_image_base64": result["output_image_base64"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Try-on failed: {str(e)}")
