"""
routes/adaptive_query.py
FastAPI route — wires HTTP requests into the 5-agent AgenticPipeline.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.agentic_pipeline import AgenticPipeline
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["adaptive-query"])

_pipeline: Optional[AgenticPipeline] = None


def _get_pipeline(use_llm: bool = False) -> AgenticPipeline:
    global _pipeline
    if _pipeline is None:
        from vectorstore.chroma_client import ChromaClient
        from graph.neo4j_client import get_neo4j_client

        chroma = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME,
        )
        chroma.connect()

        llm = None
        if use_llm:
            from llm.base import get_llm
            llm = get_llm()

        _pipeline = AgenticPipeline(
            chroma_client=chroma,
            neo4j_client=get_neo4j_client(),
            llm=llm,
        )
    return _pipeline


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
    try:
        pipeline = _get_pipeline(use_llm=bool(request.use_llm))
        result   = pipeline.run(request.question)
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
    try:
        pipeline = _get_pipeline()
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
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
