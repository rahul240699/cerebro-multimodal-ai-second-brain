"""
Text Chunking Service
Splits text into overlapping chunks for semantic search
"""

from typing import List, Dict
from app.core.config import settings


class TextChunker:
    """
    Chunk text into overlapping segments for better retrieval
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def chunk_text(self, text: str) -> List[Dict[str, any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text to chunk
        
        Returns:
            List of chunk dictionaries with 'text' and 'start' keys
        """
        
        # Split by sentences for better semantic boundaries
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        cumulative_position = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start": cumulative_position
                })
                cumulative_position += len(chunk_text)
                
                # Keep last few sentences for overlap
                overlap_sentences = []
                overlap_length = 0
                
                for sent in reversed(current_chunk):
                    if overlap_length + len(sent) <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_length += len(sent)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start": cumulative_position
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Simple sentence splitter
        For production, consider using spaCy or NLTK
        """
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Remove empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
