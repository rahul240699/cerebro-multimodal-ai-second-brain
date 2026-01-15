"""
Pydantic Schemas for API Request/Response
Clean validation and serialization
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ContentTypeEnum(str, Enum):
    """Content types for ingestion"""
    AUDIO = "audio"
    DOCUMENT = "document"
    WEB = "web"
    IMAGE = "image"


class ProcessingStatusEnum(str, Enum):
    """Processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """Request schema for creating a document"""
    title: str = Field(..., min_length=1, max_length=500)
    content_type: ContentTypeEnum
    source_url: Optional[HttpUrl] = None


class DocumentResponse(BaseModel):
    """Response schema for document metadata"""
    document_id: int
    title: str
    content_type: ContentTypeEnum
    source_url: Optional[str]
    created_at: datetime
    status: ProcessingStatusEnum
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class WebIngestRequest(BaseModel):
    """Request to ingest web content"""
    url: HttpUrl = Field(..., description="URL to scrape and ingest")
    title: Optional[str] = Field(None, description="Optional custom title")


class QueryRequest(BaseModel):
    """Request schema for querying the brain"""
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    top_k: Optional[int] = Field(20, ge=1, le=100, description="Number of results to retrieve")


class ChunkResult(BaseModel):
    """Individual chunk result from retrieval"""
    chunk_id: int
    chunk_text: str
    document_title: str
    content_type: str
    created_at: datetime
    similarity_score: float


class QueryResponse(BaseModel):
    """Response schema for query results"""
    query: str
    answer: str
    retrieved_chunks: List[ChunkResult]
    processing_time_seconds: float


class TaskStatusResponse(BaseModel):
    """Response for async task status"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
