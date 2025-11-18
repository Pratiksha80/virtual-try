# backend/run.py
import uvicorn
from main import app, PORT, HOST, find_available_port

if __name__ == "__main__":
    try:
        print(f"🚀 Starting server on {HOST}:{PORT}")
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        # Try alternative port if default is in use
        try:
            alt_port = find_available_port(PORT + 1)
            print(f"🔄 Retrying on port {alt_port}...")
            uvicorn.run(
                "main:app",
                host=HOST,
                port=alt_port,
                reload=True,
                log_level="info"
            )
        except Exception as e2:
            print(f"❌ Could not start server: {e2}")