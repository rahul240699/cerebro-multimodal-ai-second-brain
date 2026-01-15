"""
Document Processing Worker
Handles PDF and Markdown file processing
"""

import pypdf
from pathlib import Path
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, Chunk, ProcessingStatus
from app.services.embedding_service import EmbeddingService
from app.services.text_chunker import TextChunker
from app.core.config import settings


@celery_app.task(bind=True, name="process_document")
def process_document(self, document_id: int, file_content_hex: str = None):
    """
    Asynchronous document processing task
    
    Steps:
        1. Extract text from PDF or Markdown (from content, not file)
        2. Chunk the text
        3. Generate embeddings
        4. Store chunks in database
    
    Args:
        document_id: ID of the document to process
        file_content_hex: Hex-encoded file content (for containerized deployments)
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
        
        print(f"📄 Processing document: {document.title}")
        
        # Extract text based on file type
        filename = document.file_path  # Now contains filename only
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == ".pdf":
            # Decode hex content back to bytes
            if file_content_hex:
                file_bytes = bytes.fromhex(file_content_hex)
                text = _extract_pdf_from_bytes(file_bytes)
            else:
                raise ValueError("No file content provided for PDF")
        elif file_ext in [".md", ".markdown"]:
            # Decode markdown content from hex
            if file_content_hex:
                file_bytes = bytes.fromhex(file_content_hex)
                text = file_bytes.decode('utf-8')
            else:
                raise ValueError("No file content provided for Markdown")
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        print(f"✅ Text extraction complete: {len(text)} characters")
        
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
        
        print(f"✅ Document processing complete: {len(chunks)} chunks created")
        
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
        
        print(f"❌ Document processing failed: {e}")
        raise
    
    finally:
        db.close()


def _extract_pdf_text(file_path: Path) -> str:
    """Extract text from PDF file"""
    text = ""
    
    with open(file_path, "rb") as file:
        pdf_reader = pypdf.PdfReader(file)
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    return text.strip()


def _extract_pdf_from_bytes(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes
    
    Args:
        file_bytes: PDF file content as bytes
        
    Returns:
        Extracted text content
    """
    from io import BytesIO
    reader = pypdf.PdfReader(BytesIO(file_bytes))
    text = ""
    
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    return text.strip()
