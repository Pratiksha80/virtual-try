# backend/ai_engine/capture_image.py
import subprocess
import sys
import os

def capture_cloth_image(url: str, output_path: str, timeout: int = 25):
    """
    Runs capture_worker.py in a separate process to avoid Windows asyncio issues.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Run the worker as a separate Python process
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "capture_worker.py"), url, output_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"Capture failed: {result.stderr.strip()}")

        print(f"✅ Capture complete: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error in capture_cloth_image: {str(e)}")
        raise
