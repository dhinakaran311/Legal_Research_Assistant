"""
routes/adaptive_query.py  —  P0-FIX-3 update
──────────────────────────────────────────────
Now uses the shared pipeline_factory so /api/adaptive-query and /api/query
both serve from the SAME AgenticPipeline instance and ChromaDB collection.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["adaptive-query"])


class AdaptiveQueryRequest(BaseModel):
    question: str
    use_llm:  Optional[bool] = False


class AdaptiveQueryResponse(BaseModel):
    question:            str
    intent:              str
    intent_confidence:   float
    answer:              str
    sources:             List[Dict[str, Any]]
    graph_references:    List[Dict[str, Any]]
    web_sources:         List[Dict[str, Any]]
    documents_used:      int
    retrieval_strategy:  Dict[str, Any]
    confidence:          float
    processing_time_ms:  float
    metadata:            Dict[str, Any]


@router.post("/adaptive-query", response_model=AdaptiveQueryResponse)
async def adaptive_query(request: AdaptiveQueryRequest):
    """
    Full 5-agent agentic pipeline endpoint.
    Uses the shared AgenticPipeline singleton from pipeline_factory.
    """
    logger.info("POST /api/adaptive-query | question='%s'", request.question[:80])
    try:
        from pipeline_factory import get_pipeline
        pipeline = get_pipeline(use_llm=bool(request.use_llm))
        result   = await pipeline.run_async(request.question)

        return AdaptiveQueryResponse(
            question           = result.question,
            intent             = result.intent,
            intent_confidence  = result.intent_confidence,
            answer             = result.answer,
            sources            = result.sources,
            graph_references   = result.graph_references,
            web_sources        = result.web_sources,
            documents_used     = result.num_sources_retrieved,
            retrieval_strategy = result.retrieval_strategy,
            confidence         = result.confidence,
            processing_time_ms = result.processing_time_ms,
            metadata           = result.metadata,
        )
    except Exception as e:
        logger.error("adaptive_query error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adaptive-status")
async def adaptive_status() -> Dict[str, Any]:
    """Pipeline status endpoint."""
    try:
        from pipeline_factory import get_pipeline
        pipeline = get_pipeline()
        return {
            "status":  "operational",
            "version": "4.0.0",
            "pipeline": {
                "agents": [
                    "PlannerAgent",
                    "LocalResearchAgent",
                    "WebResearchAgent",
                    "ConflictCheckerAgent",
                    "SynthesisAgent",
                ],
                "web_to_db_loop":   True,
                "quality_threshold": pipeline.quality_threshold,
                "vector_store":      "ChromaDB (single source of truth)",
                "pinecone_sync":     "future — see pipeline_factory.py",
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
