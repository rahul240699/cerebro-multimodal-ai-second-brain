"""
Synthesis Service
Generates natural language responses using LLM with retrieved context
"""

from typing import List, AsyncGenerator
from openai import OpenAI
from app.models.document import Chunk
from app.core.config import settings


class SynthesisService:
    """
    Generate grounded responses using retrieved context
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_answer_stream(
        self,
        query: str,
        retrieved_chunks: List[tuple[Chunk, float]]
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response using retrieved context
        
        Args:
            query: User's question
            retrieved_chunks: List of (Chunk, score) tuples from retrieval
        
        Yields:
            Token strings as they are generated
        """
        
        # Build context from retrieved chunks
        context_parts = []
        for idx, (chunk, score) in enumerate(retrieved_chunks, 1):
            doc = chunk.document
            context_parts.append(
                f"[Source {idx}] {doc.title} ({doc.content_type.value}, {chunk.created_at.strftime('%Y-%m-%d')})\n"
                f"{chunk.chunk_text}\n"
            )
        
        context = "\n---\n".join(context_parts)
        
        # System prompt to ground the response
        system_prompt = """You are Cerebro, a personal AI assistant with perfect memory. 

Your role is to answer questions using ONLY the information provided in the context below. 

CRITICAL RULES:
1. Base your answer EXCLUSIVELY on the provided sources
2. If the context doesn't contain enough information, say "I don't have enough information in your knowledge base to answer that."
3. Cite sources by number when making specific claims (e.g., "According to Source 1...")
4. Be conversational but precise
5. NEVER make up or infer information not present in the sources

Context:
{context}
""".format(context=context)
        
        user_message = f"Question: {query}\n\nPlease answer based on the sources provided."
        
        # Stream response from LLM
        stream = self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Low temperature for factual responses
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
