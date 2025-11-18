# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from dotenv import load_dotenv
import os, bcrypt, jwt, datetime

# Load environment variables
load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
JWT_SECRET = os.getenv("JWT_SECRET", "mysecretjwtkey")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

def find_available_port(start_port=8000, max_port=8100):
    """Find an available port in the given range."""
    import socket
    port = start_port
    while port <= max_port:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('0.0.0.0', port))
                sock.close()  # Properly close the socket
                print(f"✅ Found available port: {port}")
                return port
        except OSError:
            print(f"Port {port} is in use, trying next port...")
            port += 1
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")

# MongoDB setup (with fallback for development)
try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
    client.server_info()  # Will throw an exception if cannot connect
    db = client["virtualtryon"]
    users_collection = db["users"]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"⚠️ MongoDB not available, running in development mode: {e}")
    client = None
    db = None
    users_collection = None

# Create FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Alternative Vite port
        "http://127.0.0.1:5174",
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",  # Optional: React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Server configuration
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Function to find an available port
def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")

# Update port if the default is in use
try:
    PORT = find_available_port(PORT)
except Exception as e:
    print(f"Warning: Could not find available port: {e}")
    # Keep the default port

# ----------------- MODELS -----------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ----------------- ROUTES -----------------
@app.get("/")
def home():
    """Health check route"""
    return {
        "message": "Backend is running", 
        "mongodb_status": "connected" if users_collection else "development_mode"
    }

@app.post("/register")
async def register(user: UserRegister):
    if not users_collection:
        # Development mode - accept any registration
        return {"message": "Registered in development mode", "email": user.email}
        
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    users_collection.insert_one({
        "email": user.email,
        "password": hashed,
        "created_at": datetime.datetime.utcnow()
    })
    return {"message": "Registration successful"}

@app.post("/login")
async def login(user: UserLogin):
    if not users_collection:
        # Development mode - accept any login
        token = jwt.encode(
            {"email": user.email, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)},
            JWT_SECRET,
            algorithm="HS256"
        )
        return {"access_token": token, "token_type": "bearer"}
    
    # Production mode - check credentials
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not bcrypt.checkpw(user.password.encode('utf-8'), existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = jwt.encode(
        {
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"message": "Login successful", "token": token}

# ----------------- IMPORT ONLY TRYON ROUTE (NO SSE) -----------------
from routes import tryon as tryon

app.include_router(tryon.router)

# ----------------- START SERVER -----------------
if __name__ == "__main__":
    import uvicorn
    
    # Find an available port
    port = find_available_port(PORT)
    print(f"🚀 Starting server on port {port}")
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=port,
        reload=True,
        log_level="info"
    )