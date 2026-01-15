"""
Web Content Processing Worker
Handles URL scraping and processing
"""

import requests
from bs4 import BeautifulSoup
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, Chunk, ProcessingStatus
from app.services.embedding_service import EmbeddingService
from app.services.text_chunker import TextChunker
from app.core.config import settings


@celery_app.task(bind=True, name="process_web_content")
def process_web_content(self, document_id: int):
    """
    Asynchronous web scraping and processing task
    
    Steps:
        1. Fetch webpage content
        2. Extract main text content
        3. Chunk the text
        4. Generate embeddings
        5. Store chunks in database
    
    Args:
        document_id: ID of the document to process
    """
    
    db = SessionLocal()
    embedding_service = EmbeddingService()
    text_chunker = TextChunker()
    
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.document_id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        print(f"🌐 Scraping web content: {document.source_url}")
        
        # Fetch webpage with comprehensive headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            response = requests.get(
                document.source_url, 
                headers=headers, 
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise ValueError(f"Access forbidden (403). The website {document.source_url} blocks automated access. Try copying the content manually or use a different URL.")
            elif e.response.status_code == 404:
                raise ValueError(f"Page not found (404). The URL {document.source_url} does not exist.")
            else:
                raise ValueError(f"HTTP Error {e.response.status_code}: {str(e)}")
        except requests.exceptions.Timeout:
            raise ValueError(f"Request timed out. The website {document.source_url} took too long to respond.")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
        
        print(f"✅ Web scraping complete: {len(text)} characters")
        
        # Chunk the text
        chunks = text_chunker.chunk_text(text)
        
        # Generate embeddings in batch
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
        
        # Store chunks in database
        for idx, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(
                document_id=document_id,
                chunk_text=chunk_data["text"],
                chunk_index=idx,
                embedding=embedding,
                created_at=document.created_at
            )
            db.add(chunk)
        
        # Mark document as completed
        document.status = ProcessingStatus.COMPLETED
        db.commit()
        
        print(f"✅ Web content processing complete: {len(chunks)} chunks created")
        
        return {
            "document_id": document_id,
            "status": "completed",
            "chunks_created": len(chunks)
        }
    
    except Exception as e:
        # Mark as failed and store error
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        db.commit()
        
        print(f"❌ Web content processing failed: {e}")
        raise
    
    finally:
        db.close()
