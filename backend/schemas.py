from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    summary: Optional[str] = None
    
    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    document_id: int
    filename: str
    summary: str

class QueryRequest(BaseModel):
    query: str
    document_id: Optional[int] = None  # If None, search all user documents

class QueryResponse(BaseModel):
    answer: str
    document_id: int
    filename: str
    relevant_chunks: Optional[list] = None

