"""
Image Processing Worker
Handles image captioning using Vision-LLM
"""

import os
import base64
from pathlib import Path
from openai import OpenAI
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, Chunk, ProcessingStatus
from app.services.embedding_service import EmbeddingService
from app.services.text_chunker import TextChunker
from app.core.config import settings


@celery_app.task(bind=True, name="process_image")
def process_image(self, document_id: int, file_content_hex: str):
    """
    Asynchronous image processing task
    
    Steps:
        1. Decode image from hex content
        2. Generate caption using Vision-LLM (GPT-4 Vision)
        3. Create searchable text chunk from caption
        4. Generate embedding
        5. Store in database
    
    Args:
        document_id: ID of the document to process
        file_content_hex: Image file content as hex string
    """
    
    db = SessionLocal()
    embedding_service = EmbeddingService()
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.document_id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        document.status = ProcessingStatus.PROCESSING
        db.commit()
        
        print(f"🖼️ Processing image: {document.title}")
        
        # Decode image from hex
        image_bytes = bytes.fromhex(file_content_hex)
        image_data = base64.b64encode(image_bytes).decode("utf-8")
        
        # Determine image format from filename
        image_format = Path(document.file_path).suffix.lower().replace(".", "")
        if image_format == "jpg":
            image_format = "jpeg"
        
        # Generate caption using Vision-LLM
        print("🔍 Generating image caption...")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # gpt-4o has native vision capabilities
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Provide a detailed description of this image. Include:
1. Main subjects and objects
2. Actions or activities happening
3. Setting and context
4. Any text visible in the image
5. Colors, mood, and atmosphere

Be thorough and descriptive so this caption can be used for semantic search."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        caption = response.choices[0].message.content
        print(f"✅ Caption generated: {len(caption)} characters")
        
        # Generate embedding for caption
        embedding = embedding_service.generate_embedding(caption)
        
        # Create single chunk for the image caption
        chunk = Chunk(
            document_id=document_id,
            chunk_text=f"Image: {document.title}\n\nDescription: {caption}",
            chunk_index=0,
            embedding=embedding,
            created_at=document.created_at
        )
        db.add(chunk)
        
        # Mark document as completed
        document.status = ProcessingStatus.COMPLETED
        db.commit()
        
        print(f"✅ Image processing complete")
        
        return {
            "document_id": document_id,
            "status": "completed",
            "caption": caption
        }
    
    except Exception as e:
        # Mark as failed and store error
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        db.commit()
        
        print(f"❌ Image processing failed: {e}")
        raise
    
    finally:
        db.close()
