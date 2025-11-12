from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
import PyPDF2
import pdfplumber
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

from database import SessionLocal, engine, Base
from models import User, Document
from schemas import UserCreate, UserResponse, DocumentResponse, SummaryResponse, QueryRequest, QueryResponse
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from summarizer import summarize_text, create_chunks, create_embeddings, query_documents, generate_rag_answer

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Document Summarizer API")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Extract text from PDF - improved for Thai characters
def extract_text_from_pdf(file_content: bytes) -> str:
    import io
    text = ""
    
    # Try pdfplumber first (better for Thai/unicode)
    try:
        pdf_file = io.BytesIO(file_content)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return text
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}, trying PyPDF2...")
    
    # Fallback to PyPDF2
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
    
    return text

# Extract text from TXT
def extract_text_from_txt(file_content: bytes) -> str:
    return file_content.decode('utf-8')

@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        full_name=db_user.full_name,
        is_active=db_user.is_active
    )

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

class GoogleAuthRequest(BaseModel):
    email: str
    name: str
    google_id: Optional[str] = None

@app.post("/google-auth")
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    # In production, you should verify the Google token on the frontend
    # and send the verified user information here
    try:
        email = auth_data.email
        name = auth_data.name or ""
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=name,
                hashed_password="",  # Google users don't need password
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@app.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active
    )

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check file type
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and TXT files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Extract text based on file type
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file_content)
    else:
        text = extract_text_from_txt(file_content)
    
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from document"
        )
    
    # Create chunks and embeddings for RAG
    chunks = create_chunks(text, chunk_size=1000, overlap=200)
    embeddings = []
    
    if chunks:
        embeddings = create_embeddings(chunks)
    
    # Prepare chunks data for storage
    chunks_data = [
        {"text": chunk, "embedding": emb} 
        for chunk, emb in zip(chunks, embeddings) if emb
    ]
    
    # Create document record
    db_document = Document(
        filename=file.filename,
        user_id=current_user.id,
        original_text=text,  # Store full text
        chunks=json.dumps(chunks_data) if chunks_data else None,
        embeddings=json.dumps(embeddings) if embeddings else None
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return DocumentResponse(
        id=db_document.id,
        filename=db_document.filename,
        uploaded_at=db_document.uploaded_at
    )

@app.post("/summarize/{document_id}", response_model=SummaryResponse)
async def summarize_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get full text from document
    text = document.original_text
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no text content"
        )
    
    # Generate summary using OpenAI with better prompts
    summary = summarize_text(text, max_length=300)
    
    # Update document with summary
    document.summary = summary
    db.commit()
    
    return SummaryResponse(
        document_id=document.id,
        summary=summary,
        filename=document.filename
    )

@app.get("/documents", response_model=list[DocumentResponse])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).all()
    
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            uploaded_at=doc.uploaded_at,
            summary=doc.summary
        )
        for doc in documents
    ]

@app.post("/query", response_model=QueryResponse)
async def query_document(
    query_data: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query documents using RAG. 
    If document_id is provided, searches only that document.
    Otherwise, searches all user documents.
    """
    # Get documents to search
    if query_data.document_id:
        documents = db.query(Document).filter(
            Document.id == query_data.document_id,
            Document.user_id == current_user.id
        ).all()
    else:
        documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found"
        )
    
    # Collect all chunks from documents
    all_chunks = []
    for doc in documents:
        if doc.chunks:
            try:
                chunks_data = json.loads(doc.chunks)
                # Add document info to each chunk
                for chunk_data in chunks_data:
                    chunk_data['document_id'] = doc.id
                    chunk_data['filename'] = doc.filename
                all_chunks.extend(chunks_data)
            except json.JSONDecodeError:
                continue
    
    if not all_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document chunks available for RAG queries. This usually means the documents were uploaded before the RAG feature was enabled. Please re-upload your documents to enable query functionality."
        )
    
    # Query documents using RAG
    relevant_chunks = query_documents(query_data.query, all_chunks, top_k=5)
    
    if not relevant_chunks:
        return QueryResponse(
            answer="No relevant information found in the documents.",
            document_id=query_data.document_id or documents[0].id,
            filename=documents[0].filename if documents else "Unknown"
        )
    
    # Get the primary document (first relevant chunk's document)
    primary_doc_id = relevant_chunks[0].get('document_id', documents[0].id)
    primary_doc = next((d for d in documents if d.id == primary_doc_id), documents[0])
    
    # Generate answer using RAG
    answer = generate_rag_answer(
        query_data.query, 
        relevant_chunks, 
        primary_doc.filename
    )
    
    return QueryResponse(
        answer=answer,
        document_id=primary_doc.id,
        filename=primary_doc.filename,
        relevant_chunks=[chunk['text'] for chunk in relevant_chunks[:3]]  # Return first 3 chunks
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

