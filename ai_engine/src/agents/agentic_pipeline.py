"""
AgenticPipeline  (v2)
══════════════════════════════════════════════════════════════════════════════
Full 5-agent orchestrator with self-learning web → ChromaDB storage loop.

FLOW
────
  Query
    │
    ▼
  [Agent 1] PlannerAgent
    │  • detect intent, extract acts/sections
    │  • set routing flags (use_web forced for recent/case_law)
    │
    ▼
  [Agent 2] LocalResearchAgent
    │  • search ChromaDB + Neo4j
    │  • compute quality_score
    │
    ├── quality ≥ 0.40 AND docs ≥ 2 ──────────────────────────────────────┐
    │   (sufficient local results)                                         │
    │                                                                      │
    └── quality < 0.40 OR forced web ──────────────────────────────────────▼
         │
         ▼
       [Agent 3] WebResearchAgent
         │  • scrape IndianKanoon + IndiaCode
         │
         ▼
       ★ ChromaDB STORE  ← web results saved to local DB here
         │  • next time same/similar query arrives → hits ChromaDB directly
         │  • zero web calls for repeated queries
         │
         └──────────────────────────────────────────────────────────────────┘
                                                                            │
    ▼                                                                       │
  [Agent 4] ConflictCheckerAgent  (only if needs_conflict_check)  ◄────────┘
    │  • pairwise contradiction / overlap detection
    │
    ▼
  [Agent 5] SynthesisAgent
       • merge local + web docs, rank by relevance
       • LLM answer (or rule-based fallback)
       • append conflict report

══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.planner_agent          import PlannerAgent, Plan
from agents.local_research_agent   import LocalResearchAgent, LocalResearchBundle
from agents.web_research_agent     import WebResearchAgent,   WebResearchBundle
from agents.conflict_checker_agent import ConflictCheckerAgent, ConflictReport
from agents.synthesis_agent        import SynthesisAgent, SynthesisOutput

logger = logging.getLogger(__name__)


# ── result returned to the API route ─────────────────────────────────────────

@dataclass
class PipelineResult:
    question:               str
    intent:                 str
    intent_confidence:      float
    answer:                 str
    sources:                List[Dict[str, Any]]
    graph_references:       List[Dict[str, Any]]
    web_sources:            List[Dict[str, Any]]
    num_sources_retrieved:  int
    retrieval_strategy:     Dict[str, Any]
    confidence:             float
    processing_time_ms:     float
    metadata:               Dict[str, Any] = field(default_factory=dict)


# ── pipeline ──────────────────────────────────────────────────────────────────

class AgenticPipeline:
    """
    Instantiate once at startup; call run() for each query.

    Parameters
    ──────────
    chroma_client   — chromadb.Collection (already initialised)
    neo4j_client    — Neo4j driver session (optional)
    llm             — LLM wrapper from llm/base.py (optional)
    quality_threshold — float, default 0.40
        Local quality score below this → escalate to web.
    """

    def __init__(
        self,
        chroma_client    = None,
        neo4j_client     = None,
        llm              = None,
        quality_threshold: float = 0.40,
    ):
        self.chroma             = chroma_client
        self.quality_threshold  = quality_threshold

        # instantiate all 5 agents
        self.planner   = PlannerAgent(llm=llm)
        self.local_ra  = LocalResearchAgent(
            chroma_client=chroma_client,
            neo4j_client=neo4j_client,
        )
        self.web_ra    = WebResearchAgent()
        self.conflict  = ConflictCheckerAgent(llm=llm)
        self.synthesis = SynthesisAgent(llm=llm)

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, query: str) -> PipelineResult:
        """
        Sync entry-point — kept for backward compatibility (tests, CLI).
        Internally delegates to run_async().
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already inside an event loop (e.g. pytest-asyncio):
            # run in a fresh thread to avoid 'cannot run nested event loop'
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(asyncio.run, self.run_async(query))
                return future.result()
        else:
            return asyncio.run(self.run_async(query))

    async def run_async(self, query: str) -> PipelineResult:
        """
        Async entry-point — use from FastAPI async routes.
        Web research is fully non-blocking (httpx + asyncio.gather internally).
        """
        t0 = time.perf_counter()
        logger.info("═" * 60)
        logger.info("Pipeline START | query='%s'", query[:80])

        # ── FIX #2: Legal Domain Classifier Gate ──────────────────────────────
        # This MUST run before ANY retrieval, embedding, or LLM call.
        # Non-legal queries are rejected immediately with zero LLM/DB cost.
        try:
            from guardrails.legal_classifier import (
                is_legal_query,
                legal_confidence,
                NON_LEGAL_REFUSAL,
            )
            confidence_score = legal_confidence(query)
            if not is_legal_query(query):
                logger.warning(
                    "Pipeline REJECTED (non-legal) | score=%.3f query='%s'",
                    confidence_score, query[:80],
                )
                elapsed_ms = float(round((time.perf_counter() - t0) * 1000, 1))
                return PipelineResult(
                    question              = query,
                    intent                = "non_legal",
                    intent_confidence     = 1.0,
                    answer                = NON_LEGAL_REFUSAL,
                    sources               = [],
                    graph_references      = [],
                    web_sources           = [],
                    num_sources_retrieved = 0,
                    retrieval_strategy    = {"rejected": True, "reason": "non_legal_query"},
                    confidence            = 1.0,
                    processing_time_ms    = elapsed_ms,
                    metadata              = {
                        "query_type":        "non_legal",
                        "classifier_score":  confidence_score,
                        "used_llm":          False,
                        "conflict_detected": False,
                    },
                )
        except ImportError as _e:
            logger.warning("LegalClassifier import failed (%s) — proceeding without guard", _e)

        # ── Agent 1: Plan ─────────────────────────────────────────────────────
        plan = self.planner.plan(query)
        logger.info("Agent1 PlannerAgent  | intent=%s use_web=%s conflict=%s",
                    plan.intent, plan.use_web, plan.needs_conflict_check)

        # ── Agent 2: Local search ─────────────────────────────────────────────
        local_bundle = self.local_ra.research(plan)
        logger.info("Agent2 LocalResearch | docs=%d quality=%.2f sufficient=%s",
                    len(local_bundle.all_documents),
                    local_bundle.quality_score,
                    local_bundle.is_sufficient)

        # ── Routing decision ──────────────────────────────────────────────────
        need_web = plan.use_web or not local_bundle.is_sufficient
        if not plan.use_web and not local_bundle.is_sufficient:
            plan.escalate_to_web = True
            logger.info(
                "Routing → WEB  (local quality %.2f < threshold %.2f)",
                local_bundle.quality_score, self.quality_threshold,
            )
        elif plan.use_web:
            logger.info("Routing → WEB  (forced by intent: %s)", plan.intent)
        else:
            logger.info("Routing → LOCAL  (quality sufficient)")

        # ── Agent 3: Web search + ChromaDB store (ASYNC — non-blocking) ───────
        web_bundle: WebResearchBundle = WebResearchBundle(query=query)
        if need_web:
            # ★ Awaited — does NOT block the uvicorn worker thread
            web_bundle = await self.web_ra.research_async(
                query, intent=plan.intent
            )
            logger.info("Agent3 WebResearch  | results=%d error=%s",
                        len(web_bundle.results), web_bundle.error)

            # ★ KEY STEP — store web results into ChromaDB
            if web_bundle.results and self.chroma:
                stored = self._store_web_to_chroma(web_bundle, plan)
                logger.info(
                    "ChromaDB STORE     | %d web docs stored → "
                    "future identical queries skip web",
                    stored,
                )
        else:
            logger.info("Agent3 WebResearch  | skipped (using local only)")

        # ── Agent 4: Conflict check ───────────────────────────────────────────
        all_docs = (
            local_bundle.all_documents
            + web_bundle.as_documents
        )
        conflict_report = ConflictReport()
        if plan.needs_conflict_check and all_docs:
            conflict_report = self.conflict.check(query, all_docs)
            logger.info("Agent4 ConflictCheck | has_conflicts=%s count=%d",
                        conflict_report.has_conflicts,
                        len(conflict_report.conflicts))

        # ── Agent 5: Synthesis ────────────────────────────────────────────────
        output: SynthesisOutput = self.synthesis.synthesize(
            plan            = plan,
            local_docs      = local_bundle.all_documents,
            local_graph     = local_bundle.all_graph_facts,
            web_docs        = web_bundle.as_documents,
            conflict_report = conflict_report,
        )
        logger.info("Agent5 Synthesis    | confidence=%.2f used_llm=%s",
                    output.confidence, output.used_llm)

        # ── Build result ──────────────────────────────────────────────────────
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info("Pipeline END | %.1f ms", elapsed_ms)
        logger.info("═" * 60)

        return PipelineResult(
            question              = query,
            intent                = plan.intent,
            intent_confidence     = _intent_confidence(plan),
            answer                = output.answer,
            sources               = output.sources,
            graph_references      = output.graph_references,
            web_sources           = output.web_sources,
            num_sources_retrieved = len(all_docs),
            retrieval_strategy    = _strategy_meta(
                plan, local_bundle, web_bundle, conflict_report,
            ),
            confidence            = output.confidence,
            processing_time_ms    = elapsed_ms,
            metadata              = {
                "used_llm":            output.used_llm,
                "conflict_detected":   conflict_report.has_conflicts,
                "conflict_summary":    conflict_report.summary or None,
                "local_quality":       local_bundle.quality_score,
                "web_escalated":       plan.escalate_to_web,
                "web_forced":          plan.use_web,
            },
        )

    # ── ChromaDB storage ──────────────────────────────────────────────────────

    def _store_web_to_chroma(
        self,
        bundle: WebResearchBundle,
        plan:   Plan,
    ) -> int:
        """
        Persist web results into ChromaDB so that identical/similar future
        queries are served from local storage — no web call needed.

        Returns the number of documents actually stored.
        """
        if not self.chroma or not bundle.results:
            return 0

        ids, documents, metadatas = [], [], []
        now_iso = datetime.now(timezone.utc).isoformat()

        for result in bundle.results:
            content = result.content.strip()
            if not content:
                continue

            # deterministic ID based on URL + content hash
            # → guarantees idempotent upsert (no duplicates on re-fetch)
            url_hash     = hashlib.md5(result.url.encode()).hexdigest()[:8]
            content_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
            doc_id       = f"web_{url_hash}_{content_hash}"

            act_hints = plan.sub_tasks[0].act_hints if plan.sub_tasks else []

            metadata = {
                # ── provenance ──────────────────────────────────────────────
                "source":      "web",
                "web_source":  result.web_source,   # indiankanoon | indiacode
                "url":         result.url,
                "title":       result.title,
                # ── query context ────────────────────────────────────────────
                "original_query": bundle.query[:200],
                "intent":         plan.intent,
                "act":            act_hints[0] if act_hints else "",
                # ── timestamps ──────────────────────────────────────────────
                "stored_at":   now_iso,
                "fetched_at":  now_iso,
            }

            ids.append(doc_id)
            documents.append(content)
            metadatas.append(metadata)

        if not ids:
            return 0

        try:
            # upsert → safe to call multiple times (idempotent)
            self.chroma.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.debug(
                "ChromaDB upsert OK | ids=%s", ids
            )
            return len(ids)
        except Exception as e:
            logger.error("ChromaDB store failed: %s", e)
            return 0


# ── helpers ───────────────────────────────────────────────────────────────────

def _intent_confidence(plan: Plan) -> float:
    """
    Rough proxy for how confident we are in the detected intent.
    Keyword-based intent is ~0.70; if no acts were found, drop a little.
    """
    base = 0.70
    if plan.sub_tasks and plan.sub_tasks[0].act_hints:
        base = 0.85
    if plan.intent == "general":
        base = 0.55
    return base


def _strategy_meta(
    plan:            Plan,
    local_bundle:    LocalResearchBundle,
    web_bundle:      WebResearchBundle,
    conflict_report: ConflictReport,
) -> Dict[str, Any]:
    return {
        "intent":              plan.intent,
        "is_complex":          plan.is_complex,
        "local_searched":      True,
        "local_docs_found":    len(local_bundle.all_documents),
        "local_quality":       local_bundle.quality_score,
        "local_sufficient":    local_bundle.is_sufficient,
        "web_searched":        bool(web_bundle.results),
        "web_docs_found":      len(web_bundle.results),
        "web_escalated":       plan.escalate_to_web,
        "web_forced":          plan.use_web,
        "web_stored_to_db":    bool(web_bundle.results),
        "conflict_checked":    plan.needs_conflict_check,
        "conflict_detected":   conflict_report.has_conflicts,
        # ── Legacy fields for GraphQL compatibility ──────────────────────────
        "num_documents_requested": 5,
        "min_relevance_threshold": 0.4,
        "num_documents_returned":  len(local_bundle.all_documents) + len(web_bundle.results),
        "intent_reasoning":        f"Agentic Planner: {plan.intent}",
        # ───────────────────────────────────────────────────────────────────
        "sub_tasks":           [
            {
                "type":  t.task_type,
                "acts":  t.act_hints,
                "sections": t.section_hints,
            }
            for t in plan.sub_tasks
        ],
    }
