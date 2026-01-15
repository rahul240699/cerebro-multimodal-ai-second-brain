"""
Audio Processing Worker
Handles transcription of audio files using OpenAI Whisper API
"""

import os
from openai import OpenAI
from pathlib import Path
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, Chunk, ProcessingStatus
from app.services.embedding_service import EmbeddingService
from app.services.text_chunker import TextChunker
from app.core.config import settings


@celery_app.task(bind=True, name="process_audio")
def process_audio(self, document_id: int, file_content_hex: str = None):
    """
    Asynchronous audio transcription task
    
    Steps:
        1. Load audio file from memory
        2. Transcribe using OpenAI Whisper API
        3. Chunk the transcription
        4. Generate embeddings
        5. Store chunks in database
    
    Args:
        document_id: ID of the document to process
        file_content_hex: Hex-encoded audio file content
    """
    
    db = SessionLocal()
    embedding_service = EmbeddingService()
    text_chunker = TextChunker()
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.document_id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        print(f"🎤 Transcribing audio: {document.title}")
        
        # Decode file content and create temporary file for Whisper API
        if not file_content_hex:
            raise ValueError("No audio file content provided")
        
        file_bytes = bytes.fromhex(file_content_hex)
        filename = document.file_path  # Contains original filename
        
        # Create temporary file for Whisper API (it requires a file object)
        from io import BytesIO
        audio_file = BytesIO(file_bytes)
        audio_file.name = filename  # Set name for proper file extension detection
        
        # Transcribe using OpenAI Whisper API
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        transcription_text = transcription if isinstance(transcription, str) else transcription.text
        
        print(f"✅ Transcription complete: {len(transcription_text)} characters")
        
        # Chunk the transcription
        chunks = text_chunker.chunk_text(transcription_text)
        
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
        
        print(f"✅ Audio processing complete: {len(chunks)} chunks created")
        
        # Privacy: Delete audio file after transcription
        if not settings.KEEP_AUDIO_FILES and os.path.exists(document.file_path):
            os.remove(document.file_path)
            print(f"🗑️ Audio file deleted for privacy")
        
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
        
        print(f"❌ Audio processing failed: {e}")
        raise
    
    finally:
        db.close()
