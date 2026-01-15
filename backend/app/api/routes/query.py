"""
Query API Routes
Endpoints for querying the AI brain with SSE streaming
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import time
import json
from app.core.database import get_db
from app.schemas.document import QueryRequest, ChunkResult
from app.services.retrieval_service import RetrievalService
from app.services.synthesis_service import SynthesisService

router = APIRouter()


@router.post("/chat")
async def query_brain(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the AI brain with streaming response
    Uses Server-Sent Events (SSE) for token-by-token streaming
    """
    
    retrieval_service = RetrievalService()
    synthesis_service = SynthesisService()
    
    async def generate_sse_stream():
        """Generate Server-Sent Events stream"""
        
        try:
            start_time = time.time()
            
            print(f"📥 Query received: {request.query}")
            
            # Step 1: Retrieve relevant chunks
            status_data = json.dumps({'type': 'status', 'message': 'Searching your brain...'})
            yield f"data: {status_data}\n\n"
            
            chunks_with_scores = await retrieval_service.retrieve_with_temporal_context(
                query=request.query,
                db=db,
                top_k=request.top_k or 20,
                rerank_top_n=10
            )
            
            retrieval_time = time.time() - start_time
            print(f"✅ Retrieved {len(chunks_with_scores)} chunks in {retrieval_time:.2f}s")
            
            if not chunks_with_scores:
                no_results_data = json.dumps({'type': 'error', 'message': 'No relevant information found in your knowledge base.'})
                yield f"data: {no_results_data}\n\n"
                return
            
            # Send retrieved chunks metadata
            chunks_metadata = []
            for chunk, score in chunks_with_scores:
                chunks_metadata.append({
                    "chunk_id": chunk.chunk_id,
                    "document_title": chunk.document.title,
                    "content_type": chunk.document.content_type.value,
                    "created_at": chunk.created_at.isoformat(),
                    "score": score
                })
            
            chunks_data = json.dumps({'type': 'chunks', 'chunks': chunks_metadata})
            yield f"data: {chunks_data}\n\n"
            
            # Step 2: Generate answer with streaming
            generating_data = json.dumps({'type': 'status', 'message': 'Generating answer...'})
            yield f"data: {generating_data}\n\n"
            
            print(f"🤖 Starting answer generation...")
            token_count = 0
            
            print(f"🤖 Starting answer generation...")
            token_count = 0
            async for token in synthesis_service.generate_answer_stream(
                query=request.query,
                retrieved_chunks=chunks_with_scores
            ):
                token_count += 1
                # Properly escape the token content for JSON
                token_data = json.dumps({'type': 'token', 'content': token})
                yield f"data: {token_data}\n\n"
            
            print(f"✅ Generated {token_count} tokens")
            
            # Send completion
            total_time = time.time() - start_time
            completion_data = json.dumps({'type': 'done', 'processing_time': total_time})
            yield f"data: {completion_data}\n\n"
        
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"❌ Query error: {error_msg}")
            error_data = json.dumps({'type': 'error', 'message': str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/search")
async def search_brain(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Search the brain without generating answer
    Returns raw retrieved chunks
    """
    
    retrieval_service = RetrievalService()
    
    try:
        start_time = time.time()
        
        chunks_with_scores = await retrieval_service.retrieve_with_temporal_context(
            query=request.query,
            db=db,
            top_k=request.top_k or 20,
            rerank_top_n=10
        )
        
        processing_time = time.time() - start_time
        
        # Format results
        results = []
        for chunk, score in chunks_with_scores:
            results.append(ChunkResult(
                chunk_id=chunk.chunk_id,
                chunk_text=chunk.chunk_text,
                document_title=chunk.document.title,
                content_type=chunk.document.content_type.value,
                created_at=chunk.created_at,
                similarity_score=score
            ))
        
        return {
            "query": request.query,
            "results": results,
            "processing_time_seconds": processing_time
        }
    
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")
