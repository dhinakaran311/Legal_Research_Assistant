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

_pipeline_no_llm  = None   # for use_llm=False (fast, rule-based synthesis)
_pipeline_with_llm = None  # for use_llm=True  (LLM-powered synthesis)
_pipeline_lock = threading.Lock()


def get_pipeline(use_llm: bool = False):
    """
    Return the appropriate AgenticPipeline singleton (thread-safe).

    Maintains TWO separate singletons:
      • use_llm=False → fast rule-based pipeline (no LLM overhead)
      • use_llm=True  → LLM-powered pipeline (Groq / Gemini)

    Args:
        use_llm: If True, return the LLM-backed pipeline.
                 If False (default), return the rule-based pipeline.
    """
    global _pipeline_no_llm, _pipeline_with_llm

    # Fast path — return already-built instance
    if use_llm and _pipeline_with_llm is not None:
        return _pipeline_with_llm
    if not use_llm and _pipeline_no_llm is not None:
        return _pipeline_no_llm

    with _pipeline_lock:
        if use_llm:
            if _pipeline_with_llm is None:
                logger.info("Creating LLM-powered AgenticPipeline (use_llm=True)...")
                _pipeline_with_llm = _create_pipeline(use_llm=True)
            return _pipeline_with_llm
        else:
            if _pipeline_no_llm is None:
                logger.info("Creating rule-based AgenticPipeline (use_llm=False)...")
                _pipeline_no_llm = _create_pipeline(use_llm=False)
            return _pipeline_no_llm


# ── Other singletons & shared client references ───────────────────────────────
_conversation_graph = None
_conversation_graph_lock = threading.Lock()

_crew = None
_crew_lock = threading.Lock()

_chroma_client = None
_neo4j_client  = None


def _create_pipeline(use_llm: bool):
    """Initialise ChromaDB, Neo4j, LLM, and return a fresh AgenticPipeline."""
    global _chroma_client, _neo4j_client

    from agents.agentic_pipeline import AgenticPipeline
    from vectorstore.chroma_client import ChromaClient
    from graph.neo4j_client import get_neo4j_client
    from config import settings

    logger.info("Initialising shared AgenticPipeline (ChromaDB + Neo4j)...")

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    if _chroma_client is None:
        _chroma_client = ChromaClient(
            persist_directory=settings.CHROMA_DB_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_model=settings.MODEL_NAME,
        )
        _chroma_client.connect()
        logger.info("ChromaDB connected | path=%s", settings.CHROMA_DB_PATH)

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    if _neo4j_client is None:
        try:
            _neo4j_client = get_neo4j_client()
            logger.info("Neo4j connected")
        except Exception as e:
            logger.warning("Neo4j unavailable (%s) — graph features disabled", e)

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm = None
    if use_llm:
        try:
            from llm.base import get_llm
            llm = get_llm()
            logger.info("LLM attached: %s", type(llm).__name__)
        except Exception as e:
            logger.warning("LLM init failed (%s) — rule-based fallback", e)

    pipeline = AgenticPipeline(
        chroma_client=_chroma_client,
        neo4j_client=_neo4j_client,
        llm=llm,
    )
    logger.info("AgenticPipeline ready")
    return pipeline


def get_chroma_client():
    """Return the shared ChromaDB client (initialised via get_pipeline)."""
    if _chroma_client is None:
        get_pipeline(use_llm=False)
    return _chroma_client


def get_neo4j_client():
    """Return the shared Neo4j client (initialised via get_pipeline)."""
    if _neo4j_client is None:
        get_pipeline(use_llm=False)
    return _neo4j_client


def get_conversation_graph():
    """Return the shared ConversationGraph singleton (thread-safe)."""
    global _conversation_graph

    if _conversation_graph is not None:
        return _conversation_graph

    with _conversation_graph_lock:
        if _conversation_graph is None:
            _conversation_graph = _create_conversation_graph()
    return _conversation_graph


def _create_conversation_graph():
    from conversation.graph import build_conversation_graph
    from conversation.memory import get_memory
    from llm.base import get_llm

    # Ensure shared clients are initialised
    get_pipeline(use_llm=False)

    try:
        llm = get_llm()
    except Exception as e:
        logger.warning("LLM init failed for ConversationGraph: %s", e)
        llm = None

    graph = build_conversation_graph(
        chroma_client=_chroma_client,
        neo4j_client=_neo4j_client,
        llm=llm,
        memory=get_memory(),
    )
    logger.info("ConversationGraph ready")
    return graph


def get_crew():
    """Return the shared LegalResearchCrew singleton (thread-safe)."""
    global _crew

    if _crew is not None:
        return _crew

    with _crew_lock:
        if _crew is None:
            _crew = _create_crew()
    return _crew


def _create_crew():
    try:
        from crew.legal_crew import LegalResearchCrew
        get_pipeline(use_llm=False)
        crew = LegalResearchCrew(
            chroma_client=_chroma_client,
            neo4j_client=_neo4j_client,
        )
        logger.info("LegalResearchCrew ready (available=%s)", crew.available)
        return crew
    except Exception as e:
        logger.warning("LegalResearchCrew init failed: %s", e)
        return None


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
