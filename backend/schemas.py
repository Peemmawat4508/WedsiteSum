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

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list[ChatMessage]] = []

class ChatResponse(BaseModel):
    message: str
    role: str = "assistant"

class ImageGenerationRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"  # 1024x1024, 1792x1024, or 1024x1792
    quality: Optional[str] = "standard"  # standard or hd

class ImageGenerationResponse(BaseModel):
    image_url: str
    prompt: str
    size: str

class ExportRequest(BaseModel):
    format: str  # "pdf", "txt", or "json"
    document_ids: Optional[list[int]] = None  # If None, export all documents

class GrammarCheckRequest(BaseModel):
    text: str

class GrammarCorrection(BaseModel):
    original: str
    corrected: str
    explanation: str

class GrammarCheckResponse(BaseModel):
    corrected_text: str
    corrections: list[GrammarCorrection]
    has_errors: bool

