from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import json

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_text = Column(Text)
    summary = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # RAG fields
    chunks = Column(Text)  # JSON string of document chunks
    embeddings = Column(Text)  # JSON string of embeddings
