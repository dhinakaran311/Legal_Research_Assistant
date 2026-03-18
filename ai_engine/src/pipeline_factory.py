"""
pipeline_factory.py  —  P0-FIX-3: Single pipeline, single vector store
────────────────────────────────────────────────────────────────────────
Provides a thread-safe singleton factory for AgenticPipeline so that
BOTH routes (/api/query and /api/adaptive-query) share the SAME instance
and the SAME ChromaDB vector store.

Future Pinecone sync
────────────────────
When you're ready to propagate ChromaDB data to Pinecone, add a background
task that calls _sync_to_pinecone() on a schedule (e.g. every 5 minutes).
The factory interface is designed to make this easy to plug in later without
changing the route code.

Usage:
    from pipeline_factory import get_pipeline
    pipeline = get_pipeline(use_llm=True)
    result = await pipeline.run_async(query)
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_pipeline = None
_pipeline_lock = threading.Lock()


def get_pipeline(use_llm: bool = False):
    """
    Return the shared AgenticPipeline singleton (thread-safe).

    Args:
        use_llm: If True, attach an LLM (using get_llm() factory).
                 Ignored after first creation — the singleton is reused.
    """
    global _pipeline

    # Fast path — no lock needed once created
    if _pipeline is not None:
        return _pipeline

    with _pipeline_lock:
        if _pipeline is None:
            _pipeline = _create_pipeline(use_llm)
    return _pipeline


def _create_pipeline(use_llm: bool):
    """Initialise ChromaDB, Neo4j, LLM, and return a fresh AgenticPipeline."""
    from agents.agentic_pipeline import AgenticPipeline
    from vectorstore.chroma_client import ChromaClient
    from graph.neo4j_client import get_neo4j_client
    from config import settings

    logger.info("Initialising shared AgenticPipeline (ChromaDB + Neo4j)...")

    # ── ChromaDB (primary vector store) ──────────────────────────────────────
    chroma = ChromaClient(
        persist_directory=settings.CHROMA_DB_PATH,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_model=settings.MODEL_NAME,
    )
    chroma.connect()
    logger.info("ChromaDB connected | path=%s", settings.CHROMA_DB_PATH)

    # ── Neo4j (graph knowledge) ───────────────────────────────────────────────
    try:
        neo4j_client = get_neo4j_client()
        logger.info("Neo4j connected")
    except Exception as e:
        logger.warning("Neo4j unavailable (%s) — graph features disabled", e)
        neo4j_client = None

    # ── LLM (optional) ───────────────────────────────────────────────────────
    llm = None
    if use_llm:
        try:
            from llm.base import get_llm
            llm = get_llm()
            logger.info("LLM attached: %s", type(llm).__name__)
        except Exception as e:
            logger.warning("LLM init failed (%s) — rule-based fallback", e)

    pipeline = AgenticPipeline(
        chroma_client=chroma,
        neo4j_client=neo4j_client,
        llm=llm,
    )
    logger.info("AgenticPipeline ready")
    return pipeline


# ── Future: Pinecone sync hook ─────────────────────────────────────────────────
# When you want to start propagating ChromaDB data to Pinecone, implement
# this function and call it from a FastAPI background task or APScheduler job.
#
# async def _sync_to_pinecone(batch_size: int = 100):
#     """
#     Read the latest ChromaDB docs and upsert into Pinecone.
#     Run on a schedule (e.g. every 5 min) to keep the indexes in sync.
#     """
#     from vectorstore.pinecone_client import PineconeClient
#     from config import settings
#     pipeline = get_pipeline()
#     docs = pipeline.chroma.get_all(limit=batch_size)
#     pinecone = PineconeClient(
#         api_key=settings.PINECONE_API_KEY,
#         index_name=settings.PINECONE_INDEX_NAME,
#         namespace=settings.PINECONE_NAMESPACE,
#     )
#     pinecone.connect()
#     pinecone.upsert(ids=docs["ids"], documents=docs["documents"],
#                     metadatas=docs["metadatas"])
#     logger.info("Pinecone sync | %d docs upserted", len(docs["ids"]))
