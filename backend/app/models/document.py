"""
Database Models for Documents and Chunks
PostgreSQL schema with pgvector support
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum
from app.core.database import Base


class ContentType(str, enum.Enum):
    """Types of content that can be ingested"""
    AUDIO = "audio"
    DOCUMENT = "document"
    WEB = "web"
    IMAGE = "image"


class ProcessingStatus(str, enum.Enum):
    """Processing status for async ingestion"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """
    Parent document metadata
    Stores high-level information about ingested content
    """
    __tablename__ = "documents"
    
    document_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    source_url = Column(Text, nullable=True)  # For web content
    file_path = Column(String(1000), nullable=True)  # For uploaded files
    file_size = Column(Integer, nullable=True)  # In bytes
    
    # Temporal metadata for time-based filtering
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Processing status
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # Relationship to chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.document_id}, title='{self.title}', type={self.content_type})>"


class Chunk(Base):
    """
    Text chunks with embeddings for semantic search
    Each chunk is a searchable piece of the parent document
    """
    __tablename__ = "chunks"
    
    chunk_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False, index=True)
    
    # Content
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    
    # Semantic embedding (1536 dimensions for text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=False)
    
    # Temporal metadata (inherited from parent for efficient filtering)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationship to parent document
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.chunk_id}, doc_id={self.document_id}, index={self.chunk_index})>"
