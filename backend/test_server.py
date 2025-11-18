#!/usr/bin/env python3
"""
Minimal test server
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Test server is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting test server on port 8002...")
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")

