"""
Multi-Stage Hybrid Retrieval Service
Implements temporal parsing, hybrid search, and re-ranking
"""

from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from openai import OpenAI
from app.models.document import Chunk, Document
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
import re


class RetrievalService:
    """
    Multi-stage retrieval strategy to solve time-blindness
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def retrieve_with_temporal_context(
        self,
        query: str,
        db: Session,
        top_k: int = 20,
        rerank_top_n: int = 10
    ) -> List[Tuple[Chunk, float]]:
        """
        Main retrieval pipeline with temporal awareness
        
        Args:
            query: User's natural language query
            db: Database session
            top_k: Number of initial results to retrieve
            rerank_top_n: Number of results after re-ranking
        
        Returns:
            List of (Chunk, score) tuples, ranked by relevance
        """
        
        # Step 1: Parse temporal intent from query
        date_range = await self._parse_temporal_intent(query)
        
        # Step 2: Generate query embedding for semantic search
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Step 3: Execute hybrid search with temporal filtering
        chunks = await self._hybrid_search(
            query=query,
            query_embedding=query_embedding,
            db=db,
            date_range=date_range,
            top_k=top_k
        )
        
        # Step 4: Re-rank using cross-encoder (simplified with cosine for now)
        ranked_chunks = await self._rerank_results(query, chunks, rerank_top_n)
        
        return ranked_chunks
    
    async def _parse_temporal_intent(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Use LLM to identify time-based constraints in the query
        
        Examples:
            "What did I work on last month?" -> (2025-12-01, 2025-12-31)
            "Show me documents from this week" -> (2026-01-08, 2026-01-14)
            "What's the capital of France?" -> None (no temporal constraint)
        
        Returns:
            Tuple of (start_date, end_date) or None if no temporal constraint
        """
        
        system_prompt = """You are a temporal intent parser. Analyze the user's query and determine if it has a time-based constraint.
Today's date is {today}.

If the query mentions a time period, respond with JSON:
{{"has_temporal_constraint": true, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}

If there's no time constraint, respond with:
{{"has_temporal_constraint": false}}

Examples:
- "What did I work on last month?" -> {{"has_temporal_constraint": true, "start_date": "2025-12-01", "end_date": "2025-12-31"}}
- "Documents from yesterday" -> {{"has_temporal_constraint": true, "start_date": "2026-01-13", "end_date": "2026-01-13"}}
- "What is machine learning?" -> {{"has_temporal_constraint": false}}
""".format(today=datetime.now().strftime("%Y-%m-%d"))
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for parsing
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            if result.get("has_temporal_constraint"):
                start_date = datetime.fromisoformat(result["start_date"])
                end_date = datetime.fromisoformat(result["end_date"]) + timedelta(days=1)  # Include full day
                return (start_date, end_date)
            
        except Exception as e:
            print(f"⚠️ Temporal parsing failed: {e}")
        
        return None
    
    async def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        db: Session,
        date_range: Optional[Tuple[datetime, datetime]],
        top_k: int
    ) -> List[Tuple[Chunk, float]]:
        """
        Execute parallel semantic + keyword search with temporal filtering
        
        Uses pgvector for semantic similarity and PostgreSQL full-text search
        """
        
        # Build temporal filter
        temporal_filter = ""
        if date_range:
            start_date, end_date = date_range
            temporal_filter = f"AND c.created_at >= '{start_date}' AND c.created_at < '{end_date}'"
        
        # Hybrid search query: semantic (cosine distance) + keyword (ts_rank)
        # Using RRF (Reciprocal Rank Fusion) to combine scores
        
        # Convert embedding to string format for pgvector
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        sql_query = text(f"""
            WITH semantic_results AS (
                SELECT 
                    c.chunk_id,
                    c.chunk_text,
                    c.document_id,
                    c.created_at,
                    1 - (c.embedding <=> '{embedding_str}'::vector) AS semantic_score,
                    ROW_NUMBER() OVER (ORDER BY c.embedding <=> '{embedding_str}'::vector) AS semantic_rank
                FROM chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE d.status = 'COMPLETED'::processingstatus
                {temporal_filter}
                ORDER BY c.embedding <=> '{embedding_str}'::vector
                LIMIT :top_k
            ),
            keyword_results AS (
                SELECT 
                    c.chunk_id,
                    c.chunk_text,
                    c.document_id,
                    c.created_at,
                    ts_rank(to_tsvector('english', c.chunk_text), plainto_tsquery('english', :query)) AS keyword_score,
                    ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', c.chunk_text), plainto_tsquery('english', :query)) DESC) AS keyword_rank
                FROM chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE d.status = 'COMPLETED'::processingstatus
                AND to_tsvector('english', c.chunk_text) @@ plainto_tsquery('english', :query)
                {temporal_filter}
                ORDER BY keyword_score DESC
                LIMIT :top_k
            )
            SELECT DISTINCT
                c.chunk_id,
                c.chunk_text,
                c.document_id,
                c.chunk_index,
                c.embedding,
                c.created_at,
                COALESCE(s.semantic_score, 0) * 0.7 + COALESCE(k.keyword_score, 0) * 0.3 AS combined_score
            FROM chunks c
            LEFT JOIN semantic_results s ON c.chunk_id = s.chunk_id
            LEFT JOIN keyword_results k ON c.chunk_id = k.chunk_id
            WHERE s.chunk_id IS NOT NULL OR k.chunk_id IS NOT NULL
            ORDER BY combined_score DESC
            LIMIT :top_k
        """)
        
        result = db.execute(
            sql_query,
            {
                "query": query,
                "top_k": top_k
            }
        )
        
        chunks_with_scores = []
        for row in result:
            chunk = db.query(Chunk).filter(Chunk.chunk_id == row.chunk_id).first()
            if chunk:
                chunks_with_scores.append((chunk, float(row.combined_score)))
        
        return chunks_with_scores
    
    async def _rerank_results(
        self,
        query: str,
        chunks: List[Tuple[Chunk, float]],
        top_n: int
    ) -> List[Tuple[Chunk, float]]:
        """
        Re-rank results using cross-encoder or LLM-based scoring
        For MVP, we'll use the hybrid scores directly
        
        Future: Integrate a proper cross-encoder like ms-marco-MiniLM
        """
        
        # Sort by score and take top N
        ranked = sorted(chunks, key=lambda x: x[1], reverse=True)[:top_n]
        
        return ranked
