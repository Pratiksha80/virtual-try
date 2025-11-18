#!/usr/bin/env python3
"""
Start the virtual try-on server
"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.append('.')

def start_server():
    print("🚀 Starting Virtual Try-On Server...")
    print("=" * 50)
    
    try:
        # Import the app
        from main import app
        print("✅ App imported successfully")
        
        # Start the server
        print("🌐 Starting server on http://0.0.0.0:8000")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    start_server()

