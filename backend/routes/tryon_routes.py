# routes/tryon.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import os

# Add the backend directory to Python path to ensure imports work
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🔍 Attempting to import tryon_process...")

try:
    from ai_engine.tryon_processor import process_tryon
    print("✅ Successfully imported process_tryon")
    tryon_process = process_tryon  # Alias for compatibility
except ImportError as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    raise ImportError("Could not import tryon_processor. Please check the ai_engine module.")

# Verify the function is callable
if tryon_process and callable(tryon_process):
    print("✅ tryon_process is available and callable in routes/tryon.py")
else:
    print("❌ tryon_process is NOT available or not callable in routes/tryon.py")
    print(f"tryon_process value: {tryon_process}")
    print(f"tryon_process type: {type(tryon_process)}")

router = APIRouter()

class TryonRequest(BaseModel):
    user_image: str
    cloth_image: str
    cloth_type: str = "shirt"

@router.post("/tryon")
async def virtual_tryon(request: TryonRequest):
    """Virtual try-on endpoint"""
    print("\n🚀 Virtual try-on endpoint called")
    print(f"📸 User image path: {request.user_image}")
    print(f"👕 Cloth image path: {request.cloth_image}")
    print(f"🏷️ Cloth type: {request.cloth_type}")
    
    # Verify files exist
    if not os.path.exists(request.user_image):
        print(f"❌ User image not found at path: {request.user_image}")
        raise HTTPException(status_code=400, detail="User image not found")
    
    if not os.path.exists(request.cloth_image):
        print(f"❌ Cloth image not found at path: {request.cloth_image}")
        raise HTTPException(status_code=400, detail="Cloth image not found")
    
    # Check if function is available at runtime
    if not tryon_process or not callable(tryon_process):
        print("❌ tryon_process function not available at runtime")
        raise HTTPException(
            status_code=500, 
            detail="tryon_process function not available"
        )
    
    try:
        print(f"📝 Processing request: user_image={request.user_image[:50]}..., cloth_image={request.cloth_image[:50]}..., cloth_type={request.cloth_type}")
        
        result = tryon_process(
            user_img_source=request.user_image,
            cloth_img_source=request.cloth_image,
            cloth_type=request.cloth_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        print("✅ Try-on process completed successfully")
        return result
        
    except Exception as e:
        print(f"❌ Error in virtual_tryon endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Try-on failed: {str(e)}")

