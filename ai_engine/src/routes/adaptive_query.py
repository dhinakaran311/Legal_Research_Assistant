"""
Adaptive Query Route for FastAPI
New endpoint using the Adaptive RAG Pipeline
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import logging

from pipelines.adaptive_rag import AdaptiveRAGPipeline
from graph.neo4j_client import get_neo4j_client
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["adaptive-query"])

# Initialize pipeline (singleton)
_pipeline_instance: Optional[AdaptiveRAGPipeline] = None
_neo4j_client = None  # Global Neo4j client

# Initialize Neo4j client once
def get_neo4j():
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = get_neo4j_client()
    return _neo4j_client


def get_pipeline(use_llm: bool = False) -> AdaptiveRAGPipeline:
    """Get or create pipeline instance with specified LLM mode"""
    global _pipeline_instance
    
    # Get Neo4j client
    neo4j = get_neo4j()
    
    # If switching LLM mode, recreate pipeline
    if _pipeline_instance is None or _pipeline_instance.use_llm != use_llm:
        _pipeline_instance = AdaptiveRAGPipeline(
            use_llm=use_llm,
            neo4j_client=neo4j  # Pass Neo4j client
        )
    
    return _pipeline_instance


class AdaptiveQueryRequest(BaseModel):
    """Request model for adaptive legal queries"""
    question: str
    max_docs: Optional[int] = None  # Override default retrieval count
    use_llm: Optional[bool] = False  # Enable LLM-powered answer generation


class AdaptiveQueryResponse(BaseModel):
    """Response model for adaptive legal queries"""
    question: str
    intent: str
    intent_confidence: float
    answer: str
    sources: List[Dict[str, Any]]
    graph_references: List[Dict[str, Any]]  # NEW: Graph facts from Neo4j
    documents_used: int
    retrieval_strategy: Dict[str, Any]
    confidence: float
    processing_time_ms: float
    metadata: Dict[str, Any]


@router.post("/adaptive-query", response_model=AdaptiveQueryResponse)
async def adaptive_query(request: AdaptiveQueryRequest) -> AdaptiveQueryResponse:
    """
    Process a legal query using the Adaptive RAG Pipeline
    
    The pipeline automatically:
    - Detects the intent of your question
    - Decides how many documents to retrieve (2-10 based on intent)
    - Retrieves relevant legal documents
    - Generates a structured, intent-specific answer
    
    Args:
        request: AdaptiveQueryRequest with the legal question
        
    Returns:
        AdaptiveQueryResponse with structured answer and metadata
    """
    try:
        logger.info(f"Received adaptive query: {request.question} (LLM: {request.use_llm})")
        
        # Get pipeline instance with LLM mode
        pipeline = get_pipeline(use_llm=request.use_llm)
        
        # Process query through adaptive pipeline
        kwargs = {}
        if request.max_docs:
            kwargs['max_docs'] = request.max_docs
        
        result = pipeline.process_query(request.question, **kwargs)
        
        logger.info(
            f"Adaptive query completed: intent={result.intent.value}, "
            f"docs={len(result.sources)}, time={result.processing_time_ms:.2f}ms"
        )
        
        # Convert to response format
        return AdaptiveQueryResponse(
            question=result.question,
            intent=result.intent.value,
            intent_confidence=result.intent_confidence,
            answer=result.answer,
            sources=result.sources,
            graph_references=result.graph_references,  # NEW
            documents_used=result.num_sources_retrieved,
            retrieval_strategy=result.retrieval_strategy,
            confidence=result.confidence,
            processing_time_ms=result.processing_time_ms,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing adaptive query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process adaptive query: {str(e)}"
        )


@router.get("/adaptive-status")
async def get_adaptive_status() -> Dict[str, Any]:
    """
    Get the status of the Adaptive RAG Pipeline
    
    Returns:
        Status information including pipeline configuration
    """
    try:
        pipeline = get_pipeline()
        
        # Get ChromaDB document count
        pipeline._ensure_clients()
        doc_count = pipeline.chroma_client.count()
        
        # Get cache stats
        cache_stats = {}
        if hasattr(pipeline, 'cache') and pipeline.cache:
            cache_stats = pipeline.cache.get_stats()
        
        return {
            "status": "operational",
            "version": "2.4.0",
            "pipeline": {
                "name": "Adaptive RAG",
                "intents_supported": [
                    "definitional",
                    "factual", 
                    "procedural",
                    "comparative",
                    "temporal",
                    "exploratory",
                    "unknown"
                ],
                "adaptive_retrieval_range": "2-10 documents",
                "confidence_based_thresholds": True,
                "caching_enabled": pipeline.use_cache
            },
            "database": {
                "chroma_documents": doc_count,
                "collection": settings.CHROMA_COLLECTION_NAME,
                "embedding_model": settings.MODEL_NAME
            },
            "cache": cache_stats,
            "message": f"Adaptive RAG Pipeline ready with {doc_count} legal documents."
        }
        
    except Exception as e:
        logger.error(f"Error getting adaptive status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
