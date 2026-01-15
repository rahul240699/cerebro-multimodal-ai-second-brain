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
def process_document(self, document_id: int):
    """
    Asynchronous document processing task
    
    Steps:
        1. Extract text from PDF or Markdown
        2. Chunk the text
        3. Generate embeddings
        4. Store chunks in database
    
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
        
        print(f"📄 Processing document: {document.title}")
        
        # Extract text based on file type
        file_path = Path(document.file_path)
        
        if file_path.suffix.lower() == ".pdf":
            text = _extract_pdf_text(file_path)
        elif file_path.suffix.lower() in [".md", ".markdown"]:
            text = file_path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
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
