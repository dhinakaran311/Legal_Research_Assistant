"""
Query routes for AI Engine
Handles legal question processing and retrieval
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import logging

from vectorstore.chroma_client import get_chroma_client
from embeddings.embedder import get_embedder
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for legal queries"""
    question: str
    max_results: Optional[int] = 5
    include_graph: Optional[bool] = True


class Source(BaseModel):
    """Source document model"""
    id: str
    title: str
    excerpt: str
    relevance_score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Response model for legal queries"""
    question: str
    answer: str
    sources: List[Source]
    confidence: float
    processing_time_ms: float


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Process a legal query and return relevant information
    
    Args:
        request: QueryRequest containing the legal question
        
    Returns:
        QueryResponse with answer, sources, and metadata
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Initialize ChromaDB client (create fresh instance to avoid singleton caching)
        from vectorstore.chroma_client import ChromaClient
        chroma_client = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME
        )
        chroma_client.connect()
        
        # Check if collection has documents
        doc_count = chroma_client.count()
        if doc_count == 0:
            logger.warning("ChromaDB collection is empty")
            raise HTTPException(
                status_code=503,
                detail="Knowledge base is empty. Please load legal documents first."
            )
        
        logger.info(f"Searching in collection with {doc_count} documents")
        
        # Perform semantic search
        results = chroma_client.query(
            query_texts=[request.question],
            n_results=min(request.max_results, 10)  # Cap at 10 results
        )
        
        # Process results into sources
        sources = []
        if results['ids'][0]:
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Extract title from document (first line)
                title = document.split('\n')[0] if '\n' in document else doc_id
                
                # Create excerpt (first 200 chars of content)
                excerpt = document[:200] + "..." if len(document) > 200 else document
                
                # Convert distance to relevance score (0-1, higher is better)
                # ChromaDB uses L2 distance, so smaller is better
                # We convert to similarity score
                relevance_score = max(0.0, 1.0 - (distance / 2.0))
                
                sources.append(Source(
                    id=doc_id,
                    title=title,
                    excerpt=excerpt,
                    relevance_score=round(relevance_score, 4),
                    metadata=metadata
                ))
                
                logger.info(f"Result {i+1}: {doc_id} (relevance: {relevance_score:.4f})")
        
        # Calculate confidence based on top result's relevance
        confidence = sources[0].relevance_score if sources else 0.0
        
        # Generate answer based on top sources
        if sources:
            top_source = sources[0]
            answer = f"Based on {top_source.metadata.get('source', 'legal documents')}, "
            
            # Extract key information from top result
            if 'section' in top_source.metadata:
                answer += f"Section {top_source.metadata['section']}: "
            
            # Use the excerpt as the answer
            answer += top_source.excerpt
            
            # Add reference to other relevant sources
            if len(sources) > 1:
                answer += f"\n\nAdditional relevant provisions found in {len(sources)-1} other document(s)."
        else:
            answer = "No relevant legal provisions found for your query. Please try rephrasing your question."
            confidence = 0.0
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(f"Query processed in {processing_time:.2f}ms with confidence {confidence:.4f}")
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            confidence=round(confidence, 4),
            processing_time_ms=round(processing_time, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get the current status of the AI engine
    
    Returns:
        Status information including available models and database connections
    """
    try:
        # Check ChromaDB status (create fresh instance)
        from vectorstore.chroma_client import ChromaClient
        chroma_client = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        chroma_client.connect()
        doc_count = chroma_client.count()
        vectordb_status = "operational"
        
    except Exception as e:
        logger.error(f"ChromaDB error: {str(e)}")
        doc_count = 0
        vectordb_status = "error"
    
    return {
        "status": "operational",
        "version": "2.2.0",
        "modules": {
            "vectordb": vectordb_status,
            "graphdb": "pending",
            "llm": "pending"
        },
        "database": {
            "chroma_documents": doc_count,
            "collection": settings.CHROMA_COLLECTION_NAME
        },
        "message": f"AI Engine operational with {doc_count} legal documents indexed."
    }

