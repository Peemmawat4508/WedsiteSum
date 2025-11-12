import os
from typing import Optional, List, Dict
import json

# Try to import OpenAI - optional dependency
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Initialize OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_openai_client():
    """Get OpenAI client if available"""
    if OPENAI_API_KEY and OPENAI_AVAILABLE:
        return OpenAI(api_key=OPENAI_API_KEY)
    return None

def summarize_text(text: str, max_length: int = 300) -> str:
    """
    Summarize text using OpenAI API with better prompts for Thai/English content.
    Falls back to simple extraction if API key is not set.
    """
    client = get_openai_client()
    
    if client:
        try:
            # Truncate text if too long (OpenAI has token limits)
            max_chars = 12000  # Roughly 3000 tokens
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Better for multilingual content
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that creates clear, concise summaries in the same language as the document. If the document is in Thai, respond in Thai. If in English, respond in English. If mixed, use the primary language."
                    },
                    {
                        "role": "user", 
                        "content": f"Please provide a comprehensive summary of the following document. Include key points, main topics, and important details. Keep it under {max_length} words:\n\n{text}"
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return simple_summarize(text, max_length)
    else:
        return simple_summarize(text, max_length)

def create_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks for RAG.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence or paragraph boundary
        if end < len(text):
            # Look for sentence endings
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.7:  # Only break if we're at least 70% through
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
        
        if start >= len(text):
            break
    
    return chunks

def create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for text chunks using OpenAI.
    """
    client = get_openai_client()
    
    if not client:
        return []
    
    try:
        # Batch process embeddings
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return []

def query_documents(query: str, document_chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Query documents using RAG. Returns top_k most relevant chunks.
    """
    client = get_openai_client()
    
    if not client:
        return []
    
    try:
        # Create query embedding
        query_embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = query_embedding_response.data[0].embedding
        
        # Calculate cosine similarity
        import numpy as np
        
        similarities = []
        for chunk_data in document_chunks:
            chunk_embedding = chunk_data.get('embedding', [])
            if chunk_embedding:
                # Cosine similarity
                dot_product = np.dot(query_embedding, chunk_embedding)
                norm_query = np.linalg.norm(query_embedding)
                norm_chunk = np.linalg.norm(chunk_embedding)
                
                if norm_query > 0 and norm_chunk > 0:
                    similarity = dot_product / (norm_query * norm_chunk)
                    similarities.append((similarity, chunk_data))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in similarities[:top_k]]
    
    except Exception as e:
        print(f"Error querying documents: {e}")
        return []

def generate_rag_answer(query: str, relevant_chunks: List[Dict], document_filename: str) -> str:
    """
    Generate an answer using RAG with relevant document chunks.
    """
    client = get_openai_client()
    
    if not client:
        return "OpenAI API is not configured. Please add your OPENAI_API_KEY to use RAG features."
    
    try:
        # Combine relevant chunks
        context = "\n\n".join([
            f"Chunk {i+1}:\n{chunk['text']}" 
            for i, chunk in enumerate(relevant_chunks)
        ])
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided document context. Answer in the same language as the question. If the context is in Thai and the question is in Thai, answer in Thai. Be accurate and cite information from the context."
                },
                {
                    "role": "user",
                    "content": f"""Based on the following document context from "{document_filename}", please answer this question:

Question: {query}

Document Context:
{context}

Please provide a clear, accurate answer based on the context above. If the answer cannot be found in the context, say so."""
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error generating answer: {str(e)}"

def simple_summarize(text: str, max_length: int = 200) -> str:
    """
    Simple extractive summarization as fallback.
    """
    sentences = text.split('. ')
    summary = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) <= max_length:
            summary.append(sentence)
            current_length += len(sentence) + 2
        else:
            break
    
    result = '. '.join(summary)
    if result and not result.endswith('.'):
        result += '.'
    
    return result if result else text[:max_length] + "..."
