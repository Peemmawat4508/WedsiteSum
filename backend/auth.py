from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from database import SessionLocal
from database import SessionLocal
from models import User

# Fallback in-memory user for when DB fails
# Fallback in-memory user for when DB fails
class MockUser:
    def __init__(self):
        self.id = 1
        self.email = "guest@example.com"
        self.full_name = "Guest User (Offline)"
        self.is_active = True
        self.hashed_password = ""

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(db: Session = Depends(get_db)):
    """
    Guest Mode: Always return the guest user.
    Bypasses JWT validation entirely.
    """
    guest_email = "guest@example.com"
    try:
        user = db.query(User).filter(User.email == guest_email).first()
        
        if not user:
            # Try to create guest user if it doesn't exist
            # This might fail if DB is read-only or locked
            try:
                user = User(
                    email=guest_email,
                    hashed_password=get_password_hash("guest_password"),
                    full_name="Guest User",
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            except Exception as e:
                print(f"Failed to create guest user in DB: {e}")
                # Fallback to returning a mock user so the app doesn't crash
                return MockUser()
        
        return user
    except Exception as e:
        print(f"Database error in get_current_user: {e}")
        # Ultimate fallback for 500 errors
        return MockUser()

