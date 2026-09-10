"""
Agent 2 — LocalResearchAgent
─────────────────────────────
Searches ChromaDB (vector store) + Neo4j (knowledge graph).
Returns a LocalResearchBundle that includes a quality_score so the
pipeline knows whether to escalate to the WebResearchAgent.

Quality score:
  • 0.0–0.39  → insufficient  → escalate to web
  • 0.40–0.69 → acceptable    → use local only
  • 0.70–1.00 → good          → use local only, skip web
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agents.planner_agent import Plan, SubTask, TaskType

logger = logging.getLogger(__name__)

# Below this max relevance → flag for web escalation
QUALITY_THRESHOLD = 0.73
# Minimum documents needed to be considered "found"
MIN_DOCS_THRESHOLD = 2


@dataclass
class LocalResearchResult:
    sub_task:    SubTask
    documents:   List[Dict[str, Any]] = field(default_factory=list)
    graph_facts: List[Dict[str, Any]] = field(default_factory=list)
    source:      str = "local"


@dataclass
class LocalResearchBundle:
    plan:          Plan
    results:       List[LocalResearchResult] = field(default_factory=list)
    quality_score: float = 0.0   # avg relevance of top docs; 0 = nothing found

    # ── convenience properties ────────────────────────────────────────────────

    @property
    def all_documents(self) -> List[Dict[str, Any]]:
        seen, docs = set(), []
        for r in self.results:
            for d in r.documents:
                uid = d.get("id", "")
                if uid and uid not in seen:
                    seen.add(uid)
                    docs.append(d)
        docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return docs

    @property
    def all_graph_facts(self) -> List[Dict[str, Any]]:
        seen, facts = set(), []
        for r in self.results:
            for f in r.graph_facts:
                key = f"{f.get('case_name','')}-{f.get('section','')}"
                if key not in seen:
                    seen.add(key)
                    facts.append(f)
        return facts

    @property
    def is_sufficient(self) -> bool:
        """True when local results are good enough to skip web search."""
        docs = self.all_documents
        
        # If we have retrieved cached web documents with high enough relevance,
        # we treat it as a sufficient cache hit to avoid redundant scraping.
        cached_web_docs = [
            d for d in docs 
            if d.get("metadata", {}).get("source") == "web" 
            and d.get("relevance_score", 0.0) >= 0.68
        ]
        if cached_web_docs:
            logger.info(
                "LocalResearchAgent | found %d cached web documents with relevance >= 0.68. Skipping web search.",
                len(cached_web_docs)
            )
            return True

        return (
            len(docs) >= MIN_DOCS_THRESHOLD
            and self.quality_score >= QUALITY_THRESHOLD
        )


class LocalResearchAgent:
    """
    Searches local ChromaDB + Neo4j for each sub-task in the plan.
    Computes a quality_score so the pipeline can decide whether to
    escalate to WebResearchAgent.
    """

    def __init__(self, chroma_client=None, neo4j_client=None):
        self.chroma = chroma_client
        self.neo4j  = neo4j_client

    # ── public API ────────────────────────────────────────────────────────────

    def research(self, plan: Plan) -> LocalResearchBundle:
        bundle = LocalResearchBundle(plan=plan)

        for task in plan.sub_tasks:
            result = self._execute_task(task)
            bundle.results.append(result)

        bundle.quality_score = self._compute_quality(bundle.all_documents)
        logger.info(
            "LocalResearchAgent | total_docs=%d graph_facts=%d quality=%.2f sufficient=%s",
            len(bundle.all_documents),
            len(bundle.all_graph_facts),
            bundle.quality_score,
            bundle.is_sufficient,
        )
        return bundle

    # ── private ───────────────────────────────────────────────────────────────

    def _execute_task(self, task: SubTask) -> LocalResearchResult:
        result            = LocalResearchResult(sub_task=task)
        result.documents  = self._vector_search(task)
        if task.task_type in (TaskType.STATUTE, TaskType.CASE_LAW,
                               TaskType.COMPARISON):
            result.graph_facts = self._graph_search(task)
        logger.debug(
            "LocalResearchAgent task=%-12s docs=%d facts=%d",
            task.task_type, len(result.documents), len(result.graph_facts),
        )
        return result

    def _vector_search(self, task: SubTask) -> List[Dict[str, Any]]:
        if not self.chroma:
            return []
        n     = _n_results(task)
        where = ({"act": task.act_hints[0]}
                 if len(task.act_hints) == 1 else None)
        try:
            raw = self.chroma.query(
                query_texts=[task.query], n_results=n, where=where
            )
        except Exception as e:
            logger.warning("Chroma (with filter) failed: %s — retrying bare", e)
            try:
                raw = self.chroma.query(query_texts=[task.query], n_results=n)
            except Exception as e2:
                logger.error("Chroma query failed: %s", e2)
                return []
        return _parse_chroma(raw)

    def _graph_search(self, task: SubTask) -> List[Dict[str, Any]]:
        if not self.neo4j:
            return []
        try:
            from graph.graph_queries import fetch_legal_graph_facts
            return fetch_legal_graph_facts(task.query, self.neo4j)
        except Exception as e:
            logger.warning("Graph search failed: %s", e)
            return []

    @staticmethod
    def _compute_quality(docs: List[Dict]) -> float:
        if not docs:
            return 0.0
        scores = [d.get("relevance_score", 0.0) for d in docs[:5]]
        return round(max(scores), 4)


# ── helpers ───────────────────────────────────────────────────────────────────

def _n_results(task: SubTask) -> int:
    return {
        TaskType.STATUTE:    5,
        TaskType.CASE_LAW:   4,
        TaskType.PROCEDURE:  6,
        TaskType.COMPARISON: 8,
        TaskType.GENERAL:    5,
    }.get(task.task_type, 5)


def _parse_chroma(raw: Dict) -> List[Dict[str, Any]]:
    if not raw or not raw.get("ids"):
        return []
    ids   = raw["ids"][0]
    docs  = raw.get("documents", [[]])[0]
    metas = raw.get("metadatas", [[]])[0]
    dists = raw.get("distances", [[]])[0]
    results = []
    for i, doc_id in enumerate(ids):
        # ChromaDB can return None for individual entries — guard against it
        raw_dist = dists[i] if i < len(dists) else None
        dist     = raw_dist if raw_dist is not None else 1.0
        relevance = max(0.0, round(1.0 - dist / 2.0, 4))
        content   = docs[i] if i < len(docs) else None
        content   = content if content is not None else ""   # None → empty str
        results.append({
            "id":              doc_id,
            "content":         content,
            "excerpt":         (content[:300] + "...") if len(content) > 300
                               else content,
            "metadata":        metas[i] if i < len(metas) else {},
            "relevance_score": relevance,
            "source":          "local",
        })
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results
