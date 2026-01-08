from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import Response
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
from schemas import UserCreate, UserResponse, DocumentResponse, SummaryResponse, QueryRequest, QueryResponse, ChatRequest, ChatResponse, ImageGenerationRequest, ImageGenerationResponse, ExportRequest, GrammarCheckRequest, GrammarCheckResponse
from auth import get_current_user, create_access_token, verify_password, get_password_hash
from summarizer import summarize_text, create_chunks, create_embeddings, query_documents, generate_rag_answer, chat_with_gpt, generate_image, grammar_check

app = FastAPI(title="Document Summarizer API")

# Setup startup event for table creation
@app.on_event("startup")
async def startup_event():
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
        
        # Create Guest User on startup
        db = SessionLocal()
        try:
            guest_email = "guest@example.com"
            user = db.query(User).filter(User.email == guest_email).first()
            if not user:
                print("Creating Guest User...")
                from auth import get_password_hash 
                user = User(
                    email=guest_email,
                    hashed_password=get_password_hash("guest_password"),
                    full_name="Guest User",
                    is_active=True
                )
                db.add(user)
                db.commit()
                print("Guest User created successfully")
        except Exception as e:
            print(f"Error creating guest user: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error in startup_event: {e}")

# Global Exception Handler for detailed error reporting
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_msg = f"Global Error: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": str(traceback.format_exc())}
    )

@app.get("/debug")
async def debug_endpoint():
    """Diagnostic endpoint to check environment"""
    import shutil
    
    debug_info = {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "env_vars": {
            "VERCEL": os.environ.get("VERCEL"),
            "VITE_GOOGLE_CLIENT_ID": "Set" if os.environ.get("VITE_GOOGLE_CLIENT_ID") else "Not Set",
            "OPENAI_API_KEY": "Set" if os.environ.get("OPENAI_API_KEY") else "Not Set",
        },
        "filesystem": {
            "tmp_exists": os.path.exists("/tmp"),
            "tmp_writable": os.access("/tmp", os.W_OK),
            "db_path": str(engine.url),
            "db_file_exists": os.path.exists("/tmp/documents.db") if "sqlite" in str(engine.url) else "N/A"
        }
    }
    
    # Check DB connection
    try:
        db = SessionLocal()
        user_count = db.query(User).count()
        debug_info["database"] = {"status": "connected", "user_count": user_count}
        db.close()
    except Exception as e:
        debug_info["database"] = {"status": "error", "error": str(e)}
        
    return debug_info

@app.get("/")
async def root():
    return {"status": "ok", "message": "Backend is running"}

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

# Extract text from DOCX (Word documents)
def extract_text_from_docx(file_content: bytes) -> str:
    import io
    try:
        from docx import Document as DocxDocument
        docx_file = io.BytesIO(file_content)
        doc = DocxDocument(docx_file)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except ImportError:
        raise Exception("python-docx library is required for DOCX files")
    except Exception as e:
        raise Exception(f"Error extracting text from DOCX: {str(e)}")

# Extract text from XLSX (Excel files)
def extract_text_from_xlsx(file_content: bytes) -> str:
    import io
    try:
        import openpyxl
        xlsx_file = io.BytesIO(file_content)
        workbook = openpyxl.load_workbook(xlsx_file, data_only=True)
        text = []
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text.append(f"Sheet: {sheet_name}")
            for row in sheet.iter_rows(values_only=True):
                row_text = ' | '.join(str(cell) if cell is not None else '' for cell in row)
                if row_text.strip():
                    text.append(row_text)
            text.append('')  # Empty line between sheets
        return '\n'.join(text)
    except ImportError:
        raise Exception("openpyxl library is required for XLSX files")
    except Exception as e:
        raise Exception(f"Error extracting text from XLSX: {str(e)}")

# Extract text from CSV
def extract_text_from_csv(file_content: bytes) -> str:
    import io
    import csv
    try:
        csv_file = io.BytesIO(file_content)
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                csv_file.seek(0)
                text = csv_file.read().decode(encoding)
                csv_file.seek(0)
                reader = csv.reader(io.StringIO(text))
                rows = []
                for row in reader:
                    rows.append(' | '.join(row))
                return '\n'.join(rows)
            except (UnicodeDecodeError, Exception):
                continue
        raise Exception("Could not decode CSV file")
    except Exception as e:
        raise Exception(f"Error extracting text from CSV: {str(e)}")

# Extract text from Markdown
def extract_text_from_md(file_content: bytes) -> str:
    try:
        import markdown
        md_text = file_content.decode('utf-8')
        # Convert markdown to plain text by removing markdown syntax
        html = markdown.markdown(md_text)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except ImportError:
        # Fallback: just decode and return
        return file_content.decode('utf-8')
    except Exception as e:
        return file_content.decode('utf-8', errors='ignore')

# Extract text from HTML
def extract_text_from_html(file_content: bytes) -> str:
    try:
        from bs4 import BeautifulSoup
        html_content = file_content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator='\n', strip=True)
    except ImportError:
        # Fallback: basic text extraction
        return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        return file_content.decode('utf-8', errors='ignore')

# Extract text from images using OCR
def extract_text_from_image(file_content: bytes, filename: str) -> str:
    try:
        from PIL import Image
        import pytesseract
        import io
        
        # Open image
        image = Image.open(io.BytesIO(file_content))
        
        # Perform OCR
        # Try with English and Thai languages
        try:
            text = pytesseract.image_to_string(image, lang='eng+tha')
        except:
            # Fallback to English only
            text = pytesseract.image_to_string(image, lang='eng')
        
        return text.strip()
    except ImportError:
        raise Exception("Pillow and pytesseract libraries are required for image OCR. Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")

# Main text extraction function
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file types based on extension."""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename_lower.endswith('.txt'):
        return extract_text_from_txt(file_content)
    elif filename_lower.endswith(('.docx', '.doc')):
        return extract_text_from_docx(file_content)
    elif filename_lower.endswith(('.xlsx', '.xls')):
        return extract_text_from_xlsx(file_content)
    elif filename_lower.endswith('.csv'):
        return extract_text_from_csv(file_content)
    elif filename_lower.endswith(('.md', '.markdown')):
        return extract_text_from_md(file_content)
    elif filename_lower.endswith(('.html', '.htm')):
        return extract_text_from_html(file_content)
    elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
        return extract_text_from_image(file_content, filename)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {filename_lower.split('.')[-1] if '.' in filename_lower else 'unknown'}"
        )

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
    # Read file content
    file_content = await file.read()
    
    # Extract text from file (supports multiple file types)
    try:
        text = extract_text_from_file(file_content, file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )
    
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

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

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

@app.post("/chat", response_model=ChatResponse)
async def chat(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat with GPT like ChatGPT - normal conversation without document context.
    """
    if not chat_data.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Convert conversation history to list of dicts
    history = []
    if chat_data.conversation_history:
        for msg in chat_data.conversation_history:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # Get response from GPT
    response = chat_with_gpt(chat_data.message, history)
    
    return ChatResponse(
        message=response,
        role="assistant"
    )

@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image_endpoint(
    image_data: ImageGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate an image using DALL-E based on a text prompt.
    """
    if not image_data.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty"
        )
    
    # Validate size
    valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    if image_data.size not in valid_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid size. Must be one of: {', '.join(valid_sizes)}"
        )
    
    # Validate quality
    valid_qualities = ["standard", "hd"]
    if image_data.quality not in valid_qualities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid quality. Must be one of: {', '.join(valid_qualities)}"
        )
    
    try:
        image_url = generate_image(
            prompt=image_data.prompt,
            size=image_data.size,
            quality=image_data.quality
        )
        
        return ImageGenerationResponse(
            image_url=image_url,
            prompt=image_data.prompt,
            size=image_data.size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/export")
async def export_summaries(
    export_data: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export document summaries in various formats (PDF, TXT, or JSON).
    """
    # Get documents to export
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if export_data.document_ids:
        query = query.filter(Document.id.in_(export_data.document_ids))
    
    documents = query.order_by(Document.uploaded_at.desc()).all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No documents found to export"
        )
    
    # Validate format
    valid_formats = ["pdf", "txt", "json"]
    if export_data.format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
        )
    
    format_type = export_data.format.lower()
    
    try:
        if format_type == "json":
            # Export as JSON
            export_data_list = []
            for doc in documents:
                export_data_list.append({
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "summary": doc.summary or "No summary available",
                    "text_preview": doc.original_text[:500] + "..." if doc.original_text and len(doc.original_text) > 500 else (doc.original_text or "")
                })
            
            json_content = json.dumps({
                "user": current_user.email,
                "exported_at": datetime.utcnow().isoformat(),
                "total_documents": len(documents),
                "documents": export_data_list
            }, indent=2, ensure_ascii=False)
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="summaries_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json"'
                }
            )
        
        elif format_type == "txt":
            # Export as TXT
            txt_content = f"Document Summaries Export\n"
            txt_content += f"User: {current_user.email}\n"
            txt_content += f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
            txt_content += f"Total Documents: {len(documents)}\n"
            txt_content += "=" * 80 + "\n\n"
            
            for i, doc in enumerate(documents, 1):
                txt_content += f"Document {i}: {doc.filename}\n"
                txt_content += f"Uploaded: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if doc.uploaded_at else 'N/A'}\n"
                txt_content += "-" * 80 + "\n"
                txt_content += f"Summary:\n{doc.summary or 'No summary available'}\n"
                txt_content += "\n" + "=" * 80 + "\n\n"
            
            return Response(
                content=txt_content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f'attachment; filename="summaries_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt"'
                }
            )
        
        else:  # PDF
            # Export as PDF (simple text-based PDF)
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
                from reportlab.lib.enums import TA_CENTER, TA_LEFT
                from io import BytesIO
                
                buffer = BytesIO()
                pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
                story = []
                
                # Define styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=(102, 126, 234),
                    spaceAfter=30,
                    alignment=TA_CENTER
                )
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=(51, 51, 51),
                    spaceAfter=12,
                    spaceBefore=12
                )
                normal_style = styles['Normal']
                
                # Title
                story.append(Paragraph("Document Summaries Export", title_style))
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(f"User: {current_user.email}", normal_style))
                story.append(Paragraph(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
                story.append(Paragraph(f"Total Documents: {len(documents)}", normal_style))
                story.append(Spacer(1, 0.3*inch))
                
                # Documents
                for i, document in enumerate(documents, 1):
                    if i > 1:
                        story.append(PageBreak())
                    
                    story.append(Paragraph(f"Document {i}: {document.filename}", heading_style))
                    story.append(Paragraph(f"Uploaded: {document.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if document.uploaded_at else 'N/A'}", normal_style))
                    story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph("Summary:", heading_style))
                    summary_text = document.summary or "No summary available"
                    # Replace newlines with <br/> for PDF and escape HTML
                    summary_text = summary_text.replace('\n', '<br/>').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(summary_text, normal_style))
                
                pdf_doc.build(story)
                buffer.seek(0)
                
                return Response(
                    content=buffer.read(),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="summaries_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.pdf"'
                    }
                )
            except ImportError:
                # Fallback to TXT if reportlab is not installed
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="PDF export requires reportlab library. Please install it or use TXT/JSON format."
                )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@app.post("/grammar-check", response_model=GrammarCheckResponse)
async def check_grammar(
    request: GrammarCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check and correct grammar in the provided text.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        result = grammar_check(request.text)
        
        return GrammarCheckResponse(
            corrected_text=result["corrected_text"],
            corrections=[
                {
                    "original": corr.get("original", ""),
                    "corrected": corr.get("corrected", ""),
                    "explanation": corr.get("explanation", "")
                }
                for corr in result.get("corrections", [])
            ],
            has_errors=result.get("has_errors", False)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grammar check failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

