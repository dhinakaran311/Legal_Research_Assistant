"""
CrewAI Tools
Wraps existing agents as LangChain-compatible tools for CrewAI agents.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional, Type

logger = logging.getLogger(__name__)

# ── Base tool shim (works with or without crewai installed) ───────────────────
try:
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("crewai not installed — tools running in standalone mode")

    class BaseModel:  # type: ignore
        pass

    def Field(*args, **kwargs):  # type: ignore
        return None

    class BaseTool:  # type: ignore
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            raise NotImplementedError


# ── Input schemas ─────────────────────────────────────────────────────────────

if CREWAI_AVAILABLE:
    class SearchInput(BaseModel):
        query: str = Field(description="Legal query to search for")
        n_results: int = Field(default=5, description="Number of results to return")

    class GraphInput(BaseModel):
        query: str = Field(description="Legal query for graph lookup")

    class WebInput(BaseModel):
        query: str = Field(description="Legal query to search on the web")


# ── ChromaDB Search Tool ──────────────────────────────────────────────────────

class ChromaSearchTool(BaseTool):
    name: str = "chroma_legal_search"
    description: str = (
        "Search the local ChromaDB vector store for relevant Indian legal provisions, "
        "acts, and sections. Use this first before web search."
    )

    def __init__(self, chroma_client=None, **kwargs):
        super().__init__(**kwargs)
        self._chroma = chroma_client

    def _run(self, query: str, n_results: int = 5) -> str:
        if not self._chroma:
            return json.dumps({"error": "ChromaDB not available", "results": []})
        try:
            raw = self._chroma.query(query_texts=[query], n_results=n_results)
            ids = raw.get("ids", [[]])[0]
            docs = raw.get("documents", [[]])[0]
            metas = raw.get("metadatas", [[]])[0]
            dists = raw.get("distances", [[]])[0]

            results = []
            for i, doc_id in enumerate(ids):
                dist = dists[i] if i < len(dists) else 1.0
                relevance = round(max(0.0, 1.0 - dist / 2.0), 4)
                results.append({
                    "id": doc_id,
                    "content": docs[i][:500] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "relevance_score": relevance,
                })

            logger.info("ChromaSearchTool | query='%s' results=%d", query[:40], len(results))
            return json.dumps({"results": results, "total": len(results)})
        except Exception as e:
            logger.error("ChromaSearchTool error: %s", e)
            return json.dumps({"error": str(e), "results": []})


# ── Neo4j Graph Tool ──────────────────────────────────────────────────────────

class Neo4jGraphTool(BaseTool):
    name: str = "neo4j_graph_search"
    description: str = (
        "Search the Neo4j knowledge graph for legal relationships, case citations, "
        "and cross-references between Indian acts and sections."
    )

    def __init__(self, neo4j_client=None, **kwargs):
        super().__init__(**kwargs)
        self._neo4j = neo4j_client

    def _run(self, query: str) -> str:
        if not self._neo4j:
            return json.dumps({"error": "Neo4j not available", "facts": []})
        try:
            from graph.graph_queries import fetch_legal_graph_facts
            facts = fetch_legal_graph_facts(query, self._neo4j)
            logger.info("Neo4jGraphTool | query='%s' facts=%d", query[:40], len(facts))
            return json.dumps({"facts": facts[:10], "total": len(facts)})
        except Exception as e:
            logger.error("Neo4jGraphTool error: %s", e)
            return json.dumps({"error": str(e), "facts": []})


# ── IndianKanoon Web Tool ─────────────────────────────────────────────────────

class IndianKanoonTool(BaseTool):
    name: str = "indiankanoon_search"
    description: str = (
        "Search IndianKanoon for case law, judgments, and legal precedents. "
        "Use when local search is insufficient or for recent judgments."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, query: str) -> str:
        try:
            from agents.web_research_agent import WebResearchAgent
            agent = WebResearchAgent(max_docs=4)

            # Run async in sync context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, agent._search_kanoon_async_standalone(query))
                    results = future.result(timeout=15)
            else:
                results = asyncio.run(agent._search_kanoon_async_standalone(query))

            output = [{"title": r.title, "url": r.url, "content": r.content[:400]} for r in results]
            logger.info("IndianKanoonTool | query='%s' results=%d", query[:40], len(output))
            return json.dumps({"results": output, "source": "indiankanoon"})
        except Exception as e:
            logger.error("IndianKanoonTool error: %s", e)
            return json.dumps({"error": str(e), "results": []})


# ── IndiaCode Web Tool ────────────────────────────────────────────────────────

class IndiaCodeTool(BaseTool):
    name: str = "indiacode_search"
    description: str = (
        "Search IndiaCode (indiacode.nic.in) for official Indian Acts text. "
        "Use for statutory provisions and official act content."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, query: str) -> str:
        try:
            from agents.web_research_agent import WebResearchAgent
            agent = WebResearchAgent(max_docs=4)

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, agent._search_indiacode_async_standalone(query))
                    results = future.result(timeout=15)
            else:
                results = asyncio.run(agent._search_indiacode_async_standalone(query))

            output = [{"title": r.title, "url": r.url, "content": r.content[:400]} for r in results]
            logger.info("IndiaCodeTool | query='%s' results=%d", query[:40], len(output))
            return json.dumps({"results": output, "source": "indiacode"})
        except Exception as e:
            logger.error("IndiaCodeTool error: %s", e)
            return json.dumps({"error": str(e), "results": []})
