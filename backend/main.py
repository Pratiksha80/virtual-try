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

# MongoDB setup
client = MongoClient(MONGODB_URL)
db = client["virtualtryon"]
users_collection = db["users"]

# Create FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins — adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"message": "Backend is running"}

@app.post("/register")
def register(user: UserRegister):
    """User registration"""
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({"email": user.email, "password": hashed_pw})
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    """User login and JWT token generation"""
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
from routes import tryon
app.include_router(tryon.router)
