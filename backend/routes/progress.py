from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import time

router = APIRouter()

def progress_generator():
    yield "data: Starting process...\n\n"
    time.sleep(0.5)
    yield "data: Saving user image...\n\n"
    time.sleep(0.5)
    yield "data: Capturing cloth image...\n\n"
    time.sleep(0.5)
    yield "data: Processing try-on...\n\n"
    time.sleep(0.5)
    yield "data: Completed!\n\n"

@router.get("/tryon/progress")
async def get_progress():
    return StreamingResponse(progress_generator(), media_type="text/event-stream")
