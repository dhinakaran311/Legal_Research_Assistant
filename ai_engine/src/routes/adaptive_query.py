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
        # FIX #2: Route-level legal classifier guard (defense in depth)
        from guardrails.legal_classifier import is_legal_query, legal_confidence, NON_LEGAL_REFUSAL
        classifier_score = legal_confidence(request.question)
        if not is_legal_query(request.question):
            logger.warning(
                "adaptive-query REJECTED | score=%.3f query='%s'",
                classifier_score, request.question[:80],
            )
            return AdaptiveQueryResponse(
                question           = request.question,
                intent             = "non_legal",
                intent_confidence  = 1.0,
                answer             = NON_LEGAL_REFUSAL,
                sources            = [],
                graph_references   = [],
                web_sources        = [],
                documents_used     = 0,
                retrieval_strategy = {"rejected": True, "reason": "non_legal_query"},
                confidence         = 1.0,
                processing_time_ms = 0.0,
                metadata           = {
                    "query_type":       "non_legal",
                    "classifier_score": classifier_score,
                },
            )

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
