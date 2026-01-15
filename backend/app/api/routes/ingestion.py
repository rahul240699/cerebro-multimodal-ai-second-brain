"""
Ingestion API Routes
Endpoints for uploading and processing content
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from typing import Optional
from app.core.database import get_db
from app.models.document import Document, ContentType, ProcessingStatus
from app.schemas.document import DocumentResponse, WebIngestRequest
from app.workers.audio_worker import process_audio
from app.workers.document_worker import process_document
from app.workers.web_worker import process_web_content
from app.workers.image_worker import process_image
from app.core.config import settings

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/audio", response_model=DocumentResponse)
async def ingest_audio(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process audio file (.mp3, .m4a, .wav, .ogg, .webm)
    Starts async transcription task
    """
    
    # Validate file type
    if not file.filename.endswith((".mp3", ".m4a", ".wav", ".ogg", ".webm")):
        raise HTTPException(400, "Only audio files (.mp3, .m4a, .wav, .ogg, .webm) are supported")
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > settings.MAX_AUDIO_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"Audio file too large. Max size: {settings.MAX_AUDIO_SIZE_MB}MB")
    
    # Read audio file content
    file_content = await file.read()
    
    # Create document record
    document = Document(
        title=title or file.filename,
        content_type=ContentType.AUDIO,
        file_path=file.filename,  # Store filename only
        file_size=file_size,
        status=ProcessingStatus.PENDING
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start async processing, passing file content
    process_audio.delay(document.document_id, file_content.hex())
    
    return document


@router.post("/document", response_model=DocumentResponse)
async def ingest_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process document file (.pdf, .md)
    Starts async processing task
    """
    
    # Validate file type
    if not file.filename.endswith((".pdf", ".md", ".markdown")):
        raise HTTPException(400, "Only PDF and Markdown files are supported")
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"Document too large. Max size: {settings.MAX_DOCUMENT_SIZE_MB}MB")
    
    # Read file content into memory
    file_content = await file.read()
    
    # Create document record with content stored in DB temporarily
    # For production, use S3/Cloudinary instead
    document = Document(
        title=title or file.filename,
        content_type=ContentType.DOCUMENT,
        file_path=file.filename,  # Store filename only
        file_size=file_size,
        status=ProcessingStatus.PENDING,
        extracted_text=file_content.decode('utf-8') if file.filename.endswith(('.md', '.markdown')) else None
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start async processing, passing file content via task args
    process_document.delay(document.document_id, file_content.hex())
    
    return document


@router.post("/web", response_model=DocumentResponse)
async def ingest_web(
    request: WebIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Scrape and process web content from URL
    Starts async scraping task
    """
    
    # Create document record
    document = Document(
        title=request.title or str(request.url),
        content_type=ContentType.WEB,
        source_url=str(request.url),
        status=ProcessingStatus.PENDING
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start async processing
    process_web_content.delay(document.document_id)
    
    return document


@router.post("/image", response_model=DocumentResponse)
async def ingest_image(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process image file
    Generates searchable caption using Vision-LLM
    """
    
    # Validate file type
    if not file.filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(400, "Only image files (.jpg, .png, .webp) are supported")
    
    # Save file
    file_path = UPLOAD_DIR / f"img_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    document = Document(
        title=title or file.filename,
        content_type=ContentType.IMAGE,
        file_path=str(file_path),
        status=ProcessingStatus.PENDING
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start async processing
    process_image.delay(document.document_id)
    
    return document


@router.get("/status/{document_id}", response_model=DocumentResponse)
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Check processing status of a document
    """
    
    document = db.query(Document).filter(Document.document_id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    return document
