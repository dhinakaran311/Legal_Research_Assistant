"""
routes/query.py  —  P0-FIX-3: /api/query now uses AgenticPipeline
──────────────────────────────────────────────────────────────────────
Old implementation used Pinecone + rule-based answer generation.
New implementation delegates to the shared AgenticPipeline (ChromaDB).

Both /api/query and /api/adaptive-query now:
  • use the SAME AgenticPipeline instance (via pipeline_factory)
  • use the SAME ChromaDB vector store
  • benefit from the self-learning web → ChromaDB storage loop

/api/status now reports ChromaDB doc count instead of Pinecone.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["query"])


# ── Request / Response models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Request model for legal queries."""
    question:      str
    max_results:   Optional[int]  = 5
    include_graph: Optional[bool] = True
    use_llm:       Optional[bool] = False


class QueryResponse(BaseModel):
    """Response model — compatible with the existing GraphQL resolver."""
    question:            str
    answer:              str
    sources:             List[Dict[str, Any]]
    confidence:          float
    processing_time_ms:  float
    # Extended fields (same as /api/adaptive-query so GraphQL can evolve)
    intent:              Optional[str]             = None
    intent_confidence:   Optional[float]           = None
    graph_references:    Optional[List[Dict]]      = None
    web_sources:         Optional[List[Dict]]      = None
    documents_used:      Optional[int]             = None
    retrieval_strategy:  Optional[Dict[str, Any]]  = None
    metadata:            Optional[Dict[str, Any]]  = None


# ── Route handlers ────────────────────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Process a legal query via the unified AgenticPipeline.
    Routes: intent → local ChromaDB → (web escalation if needed) → synthesis.
    """
    logger.info("POST /api/query | question='%s'", request.question[:80])

    from pipeline_factory import get_pipeline

    try:
        pipeline = get_pipeline(use_llm=bool(request.use_llm))
        result   = await pipeline.run_async(request.question)

        return QueryResponse(
            question           = result.question,
            answer             = result.answer,
            sources            = result.sources,
            confidence         = result.confidence,
            processing_time_ms = result.processing_time_ms,
            intent             = result.intent,
            intent_confidence  = result.intent_confidence,
            graph_references   = result.graph_references,
            web_sources        = result.web_sources,
            documents_used     = result.num_sources_retrieved,
            retrieval_strategy = result.retrieval_strategy,
            metadata           = result.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in /api/query: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    AI engine status — reports ChromaDB document count (Pinecone removed).
    """
    from pipeline_factory import get_pipeline
    from config import settings

    try:
        pipeline   = get_pipeline()
        doc_count  = pipeline.chroma.count() if pipeline.chroma else 0
        vec_status = "operational"
    except Exception as e:
        logger.error("ChromaDB status check failed: %s", e)
        doc_count  = 0
        vec_status = "error"

    return {
        "status":  "operational",
        "version": "3.0.0",
        "modules": {
            "vectordb": vec_status,
            "graphdb":  "operational",
            "llm":      "configured",
        },
        "database": {
            "chromadb_documents": doc_count,
            "collection":         settings.CHROMA_COLLECTION_NAME,
            # Pinecone sync: not yet enabled (future)
            "pinecone_sync":      "not_configured",
        },
        "pipeline": {
            "type":   "AgenticPipeline",
            "agents": [
                "PlannerAgent",
                "LocalResearchAgent",
                "WebResearchAgent",
                "ConflictCheckerAgent",
                "SynthesisAgent",
            ],
        },
        "message": (
            f"AI Engine operational with {doc_count} "
            "legal documents in ChromaDB."
        ),
    }
