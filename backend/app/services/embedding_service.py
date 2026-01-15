"""
Embedding Service for Semantic Indexing
Uses OpenAI text-embedding-3-small
"""

from typing import List
from openai import OpenAI
from app.core.config import settings


class EmbeddingService:
    """Generate embeddings for text chunks"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text to embed
        
        Returns:
            1536-dimensional embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        More efficient for processing many chunks
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        
        except Exception as e:
            print(f"❌ Batch embedding generation failed: {e}")
            raise
