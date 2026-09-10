"""
LangGraph Conversation Graph
Manages stateful multi-turn legal research conversations.

Graph Flow:
  START
    → resolve_query      (inject history context into query)
    → plan               (PlannerAgent — intent + routing)
    → local_research     (ChromaDB + Neo4j)
    → route              (conditional: sufficient? → synthesize : web_research)
    → [web_research]     (IndianKanoon + IndiaCode, if needed)
    → [conflict_check]   (if comparative intent)
    → synthesize         (Groq LLM answer)
    → store_memory       (save turn to ConversationMemory)
  END
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ── State definition ──────────────────────────────────────────────────────────

class ConversationState(TypedDict, total=False):
    # Session
    session_id: str
    # Input
    original_query: str
    resolved_query: str
    use_llm: bool
    is_followup: bool           # True = answer from memory, skip agents
    # Agent outputs
    plan: Any
    local_bundle: Any
    web_bundle: Any
    conflict_report: Any
    synthesis_output: Any
    # Final
    answer: str
    sources: List[Dict]
    graph_references: List[Dict]
    web_sources: List[Dict]
    confidence: float
    intent: str
    intent_confidence: float
    processing_time_ms: float
    metadata: Dict
    # Error handling
    error: Optional[str]


# ── Graph builder ─────────────────────────────────────────────────────────────

class ConversationGraph:
    """
    LangGraph-based conversation orchestrator.
    Wraps the existing 5 agents as graph nodes.
    """

    def __init__(
        self,
        chroma_client=None,
        neo4j_client=None,
        llm=None,
        memory=None,
        quality_threshold: float = 0.40,
    ):
        self.chroma = chroma_client
        self.neo4j = neo4j_client
        self.llm = llm
        self.memory = memory
        self.quality_threshold = quality_threshold

        # Import agents (reuse existing)
        from agents.planner_agent import PlannerAgent
        from agents.local_research_agent import LocalResearchAgent
        from agents.web_research_agent import WebResearchAgent
        from agents.conflict_checker_agent import ConflictCheckerAgent
        from agents.synthesis_agent import SynthesisAgent
        from conversation.query_resolver import QueryResolver

        self.planner = PlannerAgent(llm=llm)
        self.local_ra = LocalResearchAgent(
            chroma_client=chroma_client,
            neo4j_client=neo4j_client,
        )
        self.web_ra = WebResearchAgent()
        self.conflict = ConflictCheckerAgent(llm=llm)
        self.synthesis = SynthesisAgent(llm=llm)
        self.resolver = QueryResolver(llm=llm)

        # Build the LangGraph
        self._graph = self._build_graph()
        logger.info("ConversationGraph initialized")

    # ── Graph construction ────────────────────────────────────────────────────

    def _build_graph(self):
        try:
            from langgraph.graph import StateGraph, END
        except ImportError:
            logger.warning("langgraph not installed — using sequential fallback")
            return None

        g = StateGraph(ConversationState)

        # Register nodes
        g.add_node("resolve_query",   self._node_resolve_query)
        g.add_node("plan",            self._node_plan)
        g.add_node("followup_answer", self._node_followup_answer)   # fast path
        g.add_node("local_research",  self._node_local_research)
        g.add_node("web_research",    self._node_web_research)
        g.add_node("conflict_check",  self._node_conflict_check)
        g.add_node("synthesize",      self._node_synthesize)
        g.add_node("store_memory",    self._node_store_memory)

        # Edges
        g.set_entry_point("resolve_query")
        g.add_edge("resolve_query", "plan")

        # After plan: fast-path for follow-ups, full pipeline for new queries
        g.add_conditional_edges(
            "plan",
            lambda s: "followup_answer" if s.get("is_followup") else "local_research",
            {"followup_answer": "followup_answer", "local_research": "local_research"},
        )
        g.add_edge("followup_answer", "store_memory")

        # Conditional routing after local research
        g.add_conditional_edges(
            "local_research",
            self._route_after_local,
            {
                "web_research": "web_research",
                "conflict_check": "conflict_check",
                "synthesize": "synthesize",
            },
        )

        # After web research → conflict check or synthesize
        g.add_conditional_edges(
            "web_research",
            self._route_after_web,
            {
                "conflict_check": "conflict_check",
                "synthesize": "synthesize",
            },
        )

        g.add_edge("conflict_check", "synthesize")
        g.add_edge("synthesize", "store_memory")
        g.add_edge("store_memory", END)

        return g.compile()

    # ── Node implementations ──────────────────────────────────────────────────

    def _node_resolve_query(self, state: ConversationState) -> ConversationState:
        """Resolve pronouns/references using conversation history."""
        session_id = state.get("session_id", "")
        original = state["original_query"]

        if session_id and self.memory:
            history = self.memory.get_history(session_id, last_n=4)
            resolved = self.resolver.resolve(original, history)
        else:
            resolved = original

        logger.info("Node:resolve_query | '%s' → '%s'", original[:40], resolved[:40])
        return {**state, "resolved_query": resolved}

    def _node_plan(self, state: ConversationState) -> ConversationState:
        """PlannerAgent — detect intent, extract acts/sections, set routing."""
        query = state.get("resolved_query") or state["original_query"]
        plan = self.planner.plan(query)

        # Check if this is a simple follow-up that can be answered from memory
        # without running the full agent pipeline
        session_id = state.get("session_id", "")
        is_followup = False
        if session_id and self.memory:
            history = self.memory.get_history(session_id, last_n=6)
            is_followup = self._is_simple_followup(query, history)

        logger.info("Node:plan | intent=%s use_web=%s is_followup=%s",
                    plan.intent, plan.use_web, is_followup)
        return {**state, "plan": plan, "intent": plan.intent, "is_followup": is_followup}

    def _is_simple_followup(self, query: str, history) -> bool:
        """
        Detect if query is a simple follow-up that can be answered from
        conversation context without re-running all agents.
        Examples: "can you explain more?", "what does that mean?", "give an example"

        NOTE: Social pleasantries (yes/no/ok/thanks) are intentionally excluded —
        they should go through the research pipeline to avoid stale-context answers.
        """
        if len(history) < 2:
            return False

        q = query.lower().strip()

        # Only genuine elaboration / clarification requests use the fast-path
        simple_patterns = [
            "can you explain", "what does that mean", "give me an example",
            "elaborate on", "tell me more about", "can you clarify",
            "in simple terms", "in layman", "what if",
            "is that correct", "are you sure", "summarize that",
        ]
        if any(p in q for p in simple_patterns):
            return True

        # Very short queries (<= 4 words) that explicitly reference previous context
        words = q.split()
        if len(words) <= 4 and any(
            w in q for w in ["it", "this", "that", "these", "those", "them"]
        ) and len(words) >= 2:  # Must be at least a 2-word phrase, not just "yes"/"no"
            return True

        return False

    async def _node_followup_answer(self, state: ConversationState) -> ConversationState:
        """
        Fast-path: answer follow-up questions from conversation history
        without running the full agent pipeline.
        Uses Groq with conversation history as context.
        """
        query = state.get("resolved_query") or state["original_query"]
        session_id = state.get("session_id", "")

        logger.info("Node:followup_answer | answering from memory (no agents)")

        answer = ""
        if session_id and self.memory:
            history_msgs = self.memory.get_llm_messages(session_id, last_n=6)
            # Exclude the current user message (already saved before this node runs)
            history_msgs = [m for m in history_msgs
                            if not (m["role"] == "user" and m["content"] == query)]

            system = (
                "You are an expert Indian legal research assistant. "
                "Answer the follow-up question based on the conversation history. "
                "Be concise and reference previous answers where relevant. "
                "If the question requires new legal research beyond what was discussed, "
                "say: 'This needs a fresh search — please ask it as a new question.'"
            )
            messages = [{"role": "system", "content": system}]
            messages.extend(history_msgs)
            messages.append({"role": "user", "content": query})

            try:
                import os
                from groq import Groq
                client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
                resp = client.chat.completions.create(
                    model=os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant"),
                    messages=messages,
                    max_tokens=512,
                    temperature=0.3,
                )
                answer = resp.choices[0].message.content.strip()
            except Exception as e:
                logger.warning("Followup LLM failed: %s — using fallback", e)
                answer = "I couldn't process that follow-up. Please try rephrasing."
        else:
            answer = "Please ask a specific legal question to get a researched answer."

        return {
            **state,
            "answer": answer,
            "sources": [],
            "graph_references": [],
            "web_sources": [],
            "confidence": 0.85,
            "metadata": {"followup": True, "agents_skipped": True},
        }

    def _node_local_research(self, state: ConversationState) -> ConversationState:
        """LocalResearchAgent — ChromaDB + Neo4j search."""
        plan = state["plan"]
        local_bundle = self.local_ra.research(plan)
        logger.info(
            "Node:local_research | docs=%d quality=%.2f sufficient=%s",
            len(local_bundle.all_documents),
            local_bundle.quality_score,
            local_bundle.is_sufficient,
        )
        return {**state, "local_bundle": local_bundle}

    async def _node_web_research(self, state: ConversationState) -> ConversationState:
        """WebResearchAgent — async IndianKanoon + IndiaCode."""
        plan = state["plan"]
        query = state.get("resolved_query") or state["original_query"]

        web_bundle = await self.web_ra.research_async(query, intent=plan.intent)
        logger.info("Node:web_research | results=%d", len(web_bundle.results))

        # Store web results to ChromaDB (self-learning loop)
        if web_bundle.results and self.chroma:
            self._store_web_to_chroma(web_bundle, plan)

        return {**state, "web_bundle": web_bundle}

    def _node_conflict_check(self, state: ConversationState) -> ConversationState:
        """ConflictCheckerAgent — pairwise contradiction detection."""
        local_bundle = state.get("local_bundle")
        web_bundle = state.get("web_bundle")

        all_docs = []
        if local_bundle:
            all_docs.extend(local_bundle.all_documents)
        if web_bundle:
            all_docs.extend(web_bundle.as_documents)

        query = state.get("resolved_query") or state["original_query"]
        conflict_report = self.conflict.check(query, all_docs)
        logger.info("Node:conflict_check | has_conflicts=%s", conflict_report.has_conflicts)
        return {**state, "conflict_report": conflict_report}

    def _node_synthesize(self, state: ConversationState) -> ConversationState:
        """SynthesisAgent — merge all sources, generate final answer."""
        from agents.conflict_checker_agent import ConflictReport

        plan = state["plan"]
        local_bundle = state.get("local_bundle")
        web_bundle = state.get("web_bundle")
        conflict_report = state.get("conflict_report") or ConflictReport()

        local_docs = local_bundle.all_documents if local_bundle else []
        local_graph = local_bundle.all_graph_facts if local_bundle else []
        web_docs = web_bundle.as_documents if web_bundle else []

        output = self.synthesis.synthesize(
            plan=plan,
            local_docs=local_docs,
            local_graph=local_graph,
            web_docs=web_docs,
            conflict_report=conflict_report,
        )

        # Build web_sources list
        web_sources = []
        if web_bundle:
            for r in web_bundle.results:
                web_sources.append({
                    "title": r.title,
                    "url": r.url,
                    "content": r.content[:300],
                    "web_source": r.web_source,
                })

        logger.info("Node:synthesize | confidence=%.2f used_llm=%s",
                    output.confidence, output.used_llm)

        return {
            **state,
            "synthesis_output": output,
            "answer": output.answer,
            "sources": output.sources,
            "graph_references": output.graph_references,
            "web_sources": web_sources,
            "confidence": output.confidence,
        }

    def _node_store_memory(self, state: ConversationState) -> ConversationState:
        """Persist this turn to ConversationMemory."""
        session_id = state.get("session_id", "")
        if session_id and self.memory:
            plan = state.get("plan")
            self.memory.add_turn(
                session_id=session_id,
                role="assistant",
                content=state.get("answer", ""),
                metadata={
                    "intent": state.get("intent", ""),
                    "confidence": state.get("confidence", 0.0),
                    "sources_count": len(state.get("sources", [])),
                },
            )
        return state

    # ── Routing functions ─────────────────────────────────────────────────────

    def _route_after_local(self, state: ConversationState) -> str:
        """Always go to web_research for supplementary results, then synthesize."""
        plan = state["plan"]
        # Always fetch web — mirrors AgenticPipeline behavior
        # Web results enrich answers even when local quality is sufficient
        return "web_research"

    def _route_after_web(self, state: ConversationState) -> str:
        plan = state["plan"]
        if plan.needs_conflict_check:
            return "conflict_check"
        return "synthesize"

    # ── Public API ────────────────────────────────────────────────────────────

    async def run_async(
        self,
        query: str,
        session_id: str = "",
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the conversation graph for one turn.
        Returns a dict with answer, sources, metadata, etc.
        """
        t0 = time.perf_counter()

        # Save user message to memory
        if session_id and self.memory:
            self.memory.add_turn(session_id=session_id, role="user", content=query)

        initial_state: ConversationState = {
            "session_id": session_id,
            "original_query": query,
            "resolved_query": query,
            "use_llm": use_llm,
            "error": None,
        }

        try:
            if self._graph is not None:
                # LangGraph execution
                final_state = await self._graph.ainvoke(initial_state)
            else:
                # Sequential fallback (no langgraph installed)
                final_state = await self._run_sequential(initial_state)

        except Exception as e:
            logger.error("ConversationGraph error: %s", e, exc_info=True)
            final_state = {
                **initial_state,
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "graph_references": [],
                "web_sources": [],
                "confidence": 0.0,
                "intent": "unknown",
                "error": str(e),
            }

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        plan = final_state.get("plan")
        local_bundle = final_state.get("local_bundle")
        web_bundle = final_state.get("web_bundle")

        return {
            "session_id": session_id,
            "question": query,
            "resolved_query": final_state.get("resolved_query", query),
            "intent": final_state.get("intent", "unknown"),
            "intent_confidence": final_state.get("intent_confidence", 0.7),
            "answer": final_state.get("answer", ""),
            "sources": final_state.get("sources", []),
            "graph_references": final_state.get("graph_references", []),
            "web_sources": final_state.get("web_sources", []),
            "num_sources_retrieved": (
                len(local_bundle.all_documents if local_bundle else []) +
                len(web_bundle.results if web_bundle else [])
            ),
            "confidence": final_state.get("confidence", 0.0),
            "processing_time_ms": elapsed_ms,
            "metadata": {
                "used_llm": bool(
                    final_state.get("synthesis_output") and
                    getattr(final_state.get("synthesis_output"), "used_llm", False)
                ),
                "followup": final_state.get("is_followup", False),
                "agents_skipped": final_state.get("is_followup", False),
                "web_escalated": bool(plan and getattr(plan, "escalate_to_web", False)),
                "web_forced": bool(plan and getattr(plan, "use_web", False)),
                "local_quality": local_bundle.quality_score if local_bundle else 0.0,
                "conflict_detected": bool(
                    final_state.get("conflict_report") and
                    getattr(final_state.get("conflict_report"), "has_conflicts", False)
                ),
                "session_id": session_id,
            },
        }

    def run(self, query: str, session_id: str = "", use_llm: bool = True) -> Dict[str, Any]:
        """Sync wrapper for run_async."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(asyncio.run, self.run_async(query, session_id, use_llm))
                return future.result()

        return asyncio.run(self.run_async(query, session_id, use_llm))

    # ── Sequential fallback (no langgraph) ────────────────────────────────────

    async def _run_sequential(self, state: ConversationState) -> ConversationState:
        """Runs all nodes sequentially when LangGraph is not installed."""
        state = self._node_resolve_query(state)
        state = self._node_plan(state)

        # Fast path for follow-ups
        if state.get("is_followup"):
            state = await self._node_followup_answer(state)
            state = self._node_store_memory(state)
            return state

        state = self._node_local_research(state)

        plan = state["plan"]
        # Always run web — supplementary enrichment mirrors AgenticPipeline
        state = await self._node_web_research(state)

        if plan.needs_conflict_check:
            state = self._node_conflict_check(state)

        state = self._node_synthesize(state)
        state = self._node_store_memory(state)
        return state

    # ── ChromaDB web storage (self-learning loop) ─────────────────────────────

    def _store_web_to_chroma(self, web_bundle, plan) -> int:
        """Persist web results to ChromaDB for future local hits."""
        import hashlib
        from datetime import datetime, timezone

        if not self.chroma or not web_bundle.results:
            return 0

        ids, documents, metadatas = [], [], []
        now_iso = datetime.now(timezone.utc).isoformat()

        for result in web_bundle.results:
            content = result.content.strip()
            if not content:
                continue
            url_hash = hashlib.md5(result.url.encode()).hexdigest()[:8]
            content_hash = hashlib.md5(content[:200].encode()).hexdigest()[:8]
            doc_id = f"web_{url_hash}_{content_hash}"
            act_hints = plan.sub_tasks[0].act_hints if plan.sub_tasks else []
            metadatas.append({
                "source": "web",
                "web_source": result.web_source,
                "url": result.url,
                "title": result.title,
                "original_query": web_bundle.query[:200],
                "intent": plan.intent,
                "act": act_hints[0] if act_hints else "",
                "stored_at": now_iso,
            })
            ids.append(doc_id)
            documents.append(content)

        if not ids:
            return 0

        try:
            self.chroma.upsert(ids=ids, documents=documents, metadatas=metadatas)
            logger.info("ChromaDB stored %d web docs", len(ids))
            return len(ids)
        except Exception as e:
            logger.error("ChromaDB store failed: %s", e)
            return 0


# ── factory ───────────────────────────────────────────────────────────────────

def build_conversation_graph(
    chroma_client=None,
    neo4j_client=None,
    llm=None,
    memory=None,
) -> ConversationGraph:
    return ConversationGraph(
        chroma_client=chroma_client,
        neo4j_client=neo4j_client,
        llm=llm,
        memory=memory,
    )
