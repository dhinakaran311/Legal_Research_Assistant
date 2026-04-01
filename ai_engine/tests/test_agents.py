"""
tests/test_agents.py
─────────────────────
Unit tests for all 5 agents + AgenticPipeline.

Scenarios:
  1.  PlannerAgent       — intent, acts, sections, routing flags
  2.  LocalResearchAgent — quality_score, is_sufficient
  3.  WebResearchAgent   — bundle shape, as_documents
  4.  ConflictChecker    — contradiction / overlap
  5.  SynthesisAgent     — rule-based + LLM path
  6.  Pipeline (local)   — sufficient local → no web call
  7.  Pipeline (web)     — low quality → web escalation
  8.  ★ Web→DB storage   — chroma.upsert() called with correct payload
  9.  Idempotent IDs     — same URL → same doc_id (no duplicates)
  10. Forced web         — recent intent → web even if local is fine
  11. End-to-end smoke   — full pipeline run returns PipelineResult
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── stub graph module so imports don't fail ───────────────────────────────────
_gq = types.ModuleType("src.graph.graph_queries")
_gq.fetch_legal_graph_facts = lambda q, d: []
_g  = types.ModuleType("src.graph")
_g.graph_queries = _gq
sys.modules.setdefault("src.graph",               _g)
sys.modules.setdefault("src.graph.graph_queries", _gq)


# ── helpers ───────────────────────────────────────────────────────────────────

def _chroma_raw(docs, relevances):
    dists = [max(0.0, 2.0 * (1 - r)) for r in relevances]
    return {
        "ids":       [["id_" + str(i) for i in range(len(docs))]],
        "documents": [list(docs)],
        "metadatas": [[{"act": "IPC", "section": str(300 + i)}
                       for i in range(len(docs))]],
        "distances": [list(dists)],
    }


def _chroma_mock(docs, relevances):
    m = MagicMock()
    m.query.return_value = _chroma_raw(docs, relevances)
    m.upsert = MagicMock()
    return m


def _web_bundle(n=2, query="q"):
    from src.agents.web_research_agent import WebResult, WebResearchBundle
    results = [
        WebResult(
            title=f"Case {i}",
            url=f"https://indiankanoon.org/doc/{i}",
            content=f"Legal content {i} " * 25,
            web_source="indiankanoon",
            relevance_score=0.80 - i * 0.05,
        )
        for i in range(n)
    ]
    return WebResearchBundle(query=query, results=results)


# ═════════════════════════════════════════════════════════════════════════════
# 1. PlannerAgent
# ═════════════════════════════════════════════════════════════════════════════

class TestPlannerAgent(unittest.TestCase):

    def setUp(self):
        from src.agents.planner_agent import PlannerAgent
        self.pl = PlannerAgent()

    def test_factual_intent(self):
        p = self.pl.plan("What is the punishment for murder under IPC?")
        self.assertIn(p.intent, ("factual", "general"))

    def test_procedural_intent(self):
        p = self.pl.plan("How to file a consumer complaint?")
        self.assertEqual(p.intent, "procedural")

    def test_comparative_sets_conflict_flag(self):
        p = self.pl.plan("Difference between IPC and CrPC")
        self.assertEqual(p.intent, "comparative")
        self.assertTrue(p.needs_conflict_check)

    def test_case_law_forces_web(self):
        p = self.pl.plan("Supreme Court judgment on anticipatory bail")
        self.assertTrue(p.use_web)

    def test_recent_forces_web(self):
        p = self.pl.plan("Latest GST amendment 2024")
        self.assertTrue(p.use_web)

    def test_act_extracted(self):
        p = self.pl.plan("What is theft under IPC?")
        self.assertIn("IPC", p.sub_tasks[0].act_hints)

    def test_section_extracted(self):
        p = self.pl.plan("Explain section 302 IPC")
        self.assertIn("302", p.sub_tasks[0].section_hints)

    def test_use_local_always_true(self):
        p = self.pl.plan("Define cognizable offence")
        self.assertTrue(p.use_local)

    def test_escalate_to_web_starts_false(self):
        p = self.pl.plan("What is bail?")
        self.assertFalse(p.escalate_to_web)


# ═════════════════════════════════════════════════════════════════════════════
# 2. LocalResearchAgent
# ═════════════════════════════════════════════════════════════════════════════

class TestLocalResearchAgent(unittest.TestCase):

    def _plan(self, q="What is theft?"):
        from src.agents.planner_agent import PlannerAgent
        return PlannerAgent().plan(q)

    def test_high_quality_is_sufficient(self):
        from src.agents.local_research_agent import LocalResearchAgent
        ch     = _chroma_mock(["d1", "d2", "d3"], [0.9, 0.85, 0.80])
        bundle = LocalResearchAgent(chroma_client=ch).research(self._plan())
        self.assertGreaterEqual(bundle.quality_score, 0.40)
        self.assertTrue(bundle.is_sufficient)

    def test_low_quality_not_sufficient(self):
        from src.agents.local_research_agent import LocalResearchAgent
        ch     = _chroma_mock(["d1"], [0.20])
        bundle = LocalResearchAgent(chroma_client=ch).research(self._plan())
        self.assertFalse(bundle.is_sufficient)

    def test_empty_results_not_sufficient(self):
        from src.agents.local_research_agent import LocalResearchAgent
        ch = MagicMock()
        ch.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        bundle = LocalResearchAgent(chroma_client=ch).research(self._plan())
        self.assertEqual(bundle.quality_score, 0.0)
        self.assertFalse(bundle.is_sufficient)

    def test_no_chroma_returns_empty(self):
        from src.agents.local_research_agent import LocalResearchAgent
        bundle = LocalResearchAgent(chroma_client=None).research(self._plan())
        self.assertEqual(len(bundle.all_documents), 0)

    def test_deduplication(self):
        from src.agents.local_research_agent import LocalResearchAgent
        ch     = _chroma_mock(["doc"], [0.8])
        agent  = LocalResearchAgent(chroma_client=ch)
        plan   = self._plan("Compare bail under IPC and CrPC")
        bundle = agent.research(plan)
        ids    = [d["id"] for d in bundle.all_documents]
        self.assertEqual(len(ids), len(set(ids)))


# ═════════════════════════════════════════════════════════════════════════════
# 3. WebResearchAgent
# ═════════════════════════════════════════════════════════════════════════════

class TestWebResearchAgent(unittest.TestCase):

    def test_unavailable_without_deps(self):
        from src.agents.web_research_agent import WebResearchAgent
        a = WebResearchAgent()
        a._bs4 = None         # simulate missing beautifulsoup4
        self.assertFalse(a.available)

    def test_error_bundle_when_unavailable(self):
        from src.agents.web_research_agent import WebResearchAgent
        a = WebResearchAgent()
        a._bs4 = None         # simulate missing beautifulsoup4
        b = a.research("IPC 302")
        self.assertIsNotNone(b.error)
        self.assertEqual(len(b.results), 0)

    def test_as_documents_shape(self):
        from src.agents.web_research_agent import WebResult, WebResearchBundle
        r = WebResult("T", "https://indiankanoon.org/1",
                      "content " * 60, "indiankanoon", 0.75)
        docs = WebResearchBundle(query="q", results=[r]).as_documents
        self.assertEqual(len(docs), 1)
        d = docs[0]
        for key in ("id", "content", "excerpt", "metadata", "relevance_score"):
            self.assertIn(key, d)
        self.assertLessEqual(len(d["excerpt"]), 303)
        self.assertEqual(d["metadata"]["web_source"], "indiankanoon")

    def test_unique_ids_across_results(self):
        b = _web_bundle(3, "q")
        ids = [d["id"] for d in b.as_documents]
        self.assertEqual(len(ids), len(set(ids)))


# ═════════════════════════════════════════════════════════════════════════════
# 4. ConflictCheckerAgent
# ═════════════════════════════════════════════════════════════════════════════

class TestConflictCheckerAgent(unittest.TestCase):

    def setUp(self):
        from src.agents.conflict_checker_agent import ConflictCheckerAgent
        self.agent = ConflictCheckerAgent()

    def _doc(self, act, text):
        return {"id": act, "excerpt": text,
                "metadata": {"act": act}, "relevance_score": 0.8}

    def test_single_act_no_conflict(self):
        docs   = [self._doc("IPC", "Theft is punishable."),
                  self._doc("IPC", "Robbery is non-bailable.")]
        report = self.agent.check("theft", docs)
        self.assertFalse(report.has_conflicts)

    def test_contradiction_detected(self):
        docs   = [self._doc("IPC",  "The offence is bailable."),
                  self._doc("CrPC", "The offence is non-bailable.")]
        report = self.agent.check("bail offence", docs)
        self.assertTrue(report.has_conflicts)
        self.assertEqual(report.conflicts[0].type, "contradiction")

    def test_overlap_detected(self):
        docs   = [self._doc("IPC",  "penalty for assault"),
                  self._doc("CrPC", "punishment for arrest and penalty")]
        report = self.agent.check("assault", docs)
        self.assertTrue(report.has_conflicts)

    def test_empty_docs_no_crash(self):
        self.assertFalse(self.agent.check("x", []).has_conflicts)

    def test_summary_populated_on_conflict(self):
        docs   = [self._doc("IPC",     "compoundable offence"),
                  self._doc("Evidence","non-compoundable offence")]
        report = self.agent.check("compoundable", docs)
        if report.has_conflicts:
            self.assertGreater(len(report.summary), 0)


# ═════════════════════════════════════════════════════════════════════════════
# 5. SynthesisAgent
# ═════════════════════════════════════════════════════════════════════════════

class TestSynthesisAgent(unittest.TestCase):

    def setUp(self):
        from src.agents.synthesis_agent        import SynthesisAgent
        from src.agents.conflict_checker_agent import ConflictReport
        from src.agents.planner_agent          import PlannerAgent
        self.SA      = SynthesisAgent
        self.Report  = ConflictReport
        self.planner = PlannerAgent()

    def _doc(self, i=0, src="local"):
        return {
            "id": f"d{i}", "content": f"content {i} " * 30,
            "excerpt": f"excerpt {i}",
            "relevance_score": 0.8 - i * 0.05,
            "source": src,
            "metadata": {"act": "IPC", "section": str(300 + i), "source": src},
        }

    def test_rule_based_non_empty(self):
        plan   = self.planner.plan("What is the punishment for theft?")
        output = self.SA().synthesize(
            plan=plan, local_docs=[self._doc(0), self._doc(1)],
            local_graph=[], web_docs=[], conflict_report=self.Report(),
        )
        self.assertGreater(len(output.answer), 0)
        self.assertFalse(output.used_llm)

    def test_no_docs_fallback_message(self):
        plan   = self.planner.plan("anything")
        output = self.SA().synthesize(
            plan=plan, local_docs=[], local_graph=[],
            web_docs=[], conflict_report=self.Report(),
        )
        self.assertIn("No relevant", output.answer)

    def test_conflict_appended(self):
        from src.agents.conflict_checker_agent import ConflictReport, Conflict
        plan   = self.planner.plan("Compare IPC bail vs CrPC bail")
        report = ConflictReport(
            conflicts=[Conflict("contradiction", "IPC", "CrPC",
                                "IPC bailable; CrPC non-bailable", "CrPC prevails")],
            summary="⚠ 1 conflict", has_conflicts=True,
        )
        output = self.SA().synthesize(
            plan=plan, local_docs=[self._doc(0)],
            local_graph=[], web_docs=[], conflict_report=report,
        )
        self.assertIn("conflict", output.answer.lower())

    def test_web_docs_in_web_sources(self):
        plan  = self.planner.plan("Latest GST 2024")
        wd    = self._doc(0, "web")
        wd["metadata"]["url"] = "https://indiankanoon.org/doc/1"
        output = self.SA().synthesize(
            plan=plan, local_docs=[], local_graph=[],
            web_docs=[wd], conflict_report=self.Report(),
        )
        self.assertGreater(len(output.web_sources), 0)

    def test_llm_called_when_provided(self):
        llm = MagicMock()
        llm.generate.return_value = "LLM answer."
        plan   = self.planner.plan("IPC 302")
        output = self.SA(llm=llm).synthesize(
            plan=plan, local_docs=[self._doc(0)],
            local_graph=[], web_docs=[], conflict_report=self.Report(),
        )
        llm.generate.assert_called_once()
        self.assertTrue(output.used_llm)


# ═════════════════════════════════════════════════════════════════════════════
# 6–11. AgenticPipeline
# ═════════════════════════════════════════════════════════════════════════════

class TestAgenticPipeline(unittest.TestCase):

    def _pipeline(self, chroma):
        from src.agents.agentic_pipeline import AgenticPipeline
        return AgenticPipeline(chroma_client=chroma, llm=None)

    # ── 6. local-only path ────────────────────────────────────────────────────
    def test_local_sufficient_skips_web(self):
        ch = _chroma_mock(["d1","d2","d3"], [0.9, 0.85, 0.80])
        pl = self._pipeline(ch)
        with patch.object(pl.web_ra, "research") as mock_web:
            pl.run("What is IPC 378?")
        mock_web.assert_not_called()
        ch.upsert.assert_not_called()

    # ── 7. low quality → web escalation ──────────────────────────────────────
    def test_low_quality_calls_web(self):
        ch = _chroma_mock(["weak"], [0.10])
        pl = self._pipeline(ch)
        async def _fake_web_async(query, intent="general"):
            return _web_bundle(2)
        pl.web_ra.research_async = _fake_web_async
        result = pl.run("What is IPC 302?")
        self.assertTrue(result.metadata["web_escalated"])

    # ── ★ 8. web → DB storage ─────────────────────────────────────────────────
    def test_web_stored_in_chroma(self):
        ch = _chroma_mock(["weak"], [0.05])
        pl = self._pipeline(ch)
        wb = _web_bundle(2, "bail under IPC")
        async def _fake_web_async(query, intent="general"):
            return wb
        pl.web_ra.research_async = _fake_web_async
        pl.run("Latest bail law IPC")

        ch.upsert.assert_called_once()
        kw = ch.upsert.call_args.kwargs
        self.assertEqual(len(kw["ids"]),       2)
        self.assertEqual(len(kw["documents"]), 2)
        for m in kw["metadatas"]:
            self.assertEqual(m["source"],   "web")
            self.assertIn("url",            m)
            self.assertIn("stored_at",      m)
            self.assertIn("original_query", m)
            self.assertIn("intent",         m)

    # ── 9. idempotent IDs ─────────────────────────────────────────────────────
    def test_stored_ids_are_deterministic(self):
        from src.agents.agentic_pipeline import AgenticPipeline
        from src.agents.web_research_agent import WebResult, WebResearchBundle
        ch   = _chroma_mock(["w"], [0.05])
        pl   = AgenticPipeline(chroma_client=ch, llm=None)
        plan = MagicMock(); plan.intent = "general"; plan.sub_tasks = []
        r    = WebResult("T", "https://a.com/doc", "content " * 30,
                         "indiankanoon", 0.7)
        b1   = WebResearchBundle(query="q1", results=[r])
        b2   = WebResearchBundle(query="q2", results=[r])
        pl._store_web_to_chroma(b1, plan)
        pl._store_web_to_chroma(b2, plan)
        id1 = ch.upsert.call_args_list[0].kwargs["ids"][0]
        id2 = ch.upsert.call_args_list[1].kwargs["ids"][0]
        self.assertEqual(id1, id2,
                         "Same URL must produce same doc_id (idempotent upsert)")

    # ── 10. forced web for recent intent ─────────────────────────────────────
    def test_forced_web_for_recent_intent(self):
        ch = _chroma_mock(["d1","d2","d3"], [0.9, 0.85, 0.80])
        pl = self._pipeline(ch)
        empty_wb = __import__(
            "agents.web_research_agent",
            fromlist=["WebResearchBundle"]
        ).WebResearchBundle(query="q", results=[])
        async def _fake_web_async(query, intent="general"):
            return empty_wb
        pl.web_ra.research_async = _fake_web_async
        result = pl.run("Latest GST amendment 2024")
        self.assertTrue(result.metadata["web_forced"])

    # ── 11. end-to-end smoke ──────────────────────────────────────────────────
    def test_full_run_returns_pipeline_result(self):
        from agents.agentic_pipeline import PipelineResult
        ch     = _chroma_mock(["d1","d2"], [0.75, 0.65])
        result = self._pipeline(ch).run("Section 420 IPC")
        self.assertIsInstance(result, PipelineResult)
        self.assertGreater(len(result.answer), 0)
        self.assertGreater(result.processing_time_ms, 0)
        for key in ("intent", "local_searched", "local_docs_found",
                    "local_quality", "local_sufficient", "web_searched",
                    "web_docs_found", "web_stored_to_db", "conflict_checked"):
            self.assertIn(key, result.retrieval_strategy, f"Missing: {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
