"""
Agent 5 — SynthesisAgent
─────────────────────────
Combines local documents, web results, graph facts, and conflict report
into a single coherent answer.

• LLM path   — intent-specific prompt template → polished answer
• Rule-based — structured formatter when no LLM is available
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agents.planner_agent import Plan
from agents.conflict_checker_agent import ConflictReport

logger = logging.getLogger(__name__)

MAX_CTX_CHARS = 2500  # Groq 70b can handle more context — was 1000, too aggressive

RELEVANCE_FILTER_THRESHOLD = 0.40  # lowered — 0.65 was too aggressive, dropped relevant docs

_PROMPTS: Dict[str, str] = {
    "factual": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Read ALL documents below carefully\n"
        "- ONLY use documents that are DIRECTLY relevant to the question asked\n"
        "- IGNORE documents about unrelated topics (e.g. if asked about FIR, ignore bail sections)\n"
        "- State the specific legal facts, cite Act name and section number\n"
        "- If no document answers the question, say so clearly\n\n"
        "Legal Documents:\n{context}\n\n"
        "Answer (cite sections, under 300 words):"
    ),
    "procedural": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Read ALL documents below carefully\n"
        "- ONLY use documents that describe the SPECIFIC procedure asked about\n"
        "- IGNORE documents about unrelated procedures or topics\n"
        "- Give a clear numbered step-by-step procedure\n"
        "- Cite the relevant section and act for each step\n"
        "- If the documents don't cover this procedure, say so and give general guidance\n\n"
        "Legal Documents:\n{context}\n\n"
        "Step-by-step procedure:"
    ),
    "comparative": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Compare the legal concepts clearly using the documents\n"
        "- Use structured format: Key Differences, then each point\n"
        "- Cite Act names and section numbers\n\n"
        "Legal Documents:\n{context}\n\n"
        "Comparison:"
    ),
    "exploratory": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Give a comprehensive overview using the documents\n"
        "- Organise into: Definition, Key Provisions, Important Points\n"
        "- Cite multiple sections as relevant\n\n"
        "Legal Documents:\n{context}\n\n"
        "Overview:"
    ),
    "case_law": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Summarise relevant judgments and case law from the documents\n"
        "- Mention case names, years, and key holdings\n\n"
        "Legal Documents:\n{context}\n\n"
        "Case Law Summary:"
    ),
    "recent": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Summarise the latest legal developments from the documents\n"
        "- Highlight what is new or has changed\n\n"
        "Legal Documents:\n{context}\n\n"
        "Latest Developments:"
    ),
    "general": (
        "You are an expert in Indian law.\n"
        "The user asked: {question}\n\n"
        "INSTRUCTIONS:\n"
        "- Read ALL documents and identify which ones answer the question\n"
        "- IGNORE documents that are not relevant to the question\n"
        "- Answer clearly, cite Act names and section numbers\n"
        "- If documents don't answer the question, say so\n\n"
        "Legal Documents:\n{context}\n\n"
        "Answer:"
    ),
}


@dataclass
class SynthesisOutput:
    answer:           str
    sources:          List[Dict[str, Any]]  = field(default_factory=list)
    graph_references: List[Dict[str, Any]]  = field(default_factory=list)
    web_sources:      List[Dict[str, Any]]  = field(default_factory=list)
    conflict_report:  Optional[ConflictReport] = None
    confidence:       float = 0.0
    used_llm:         bool  = False


class SynthesisAgent:
    def __init__(self, llm=None):
        self.llm = llm

    # ── public API ────────────────────────────────────────────────────────────

    def synthesize(
        self,
        plan:            Plan,
        local_docs:      List[Dict[str, Any]],
        local_graph:     List[Dict[str, Any]],
        web_docs:        List[Dict[str, Any]],
        conflict_report: ConflictReport,
    ) -> SynthesisOutput:

        all_docs   = _merge_and_rank(local_docs, web_docs)
        sources    = _build_sources(all_docs)
        # Tag web sources correctly (docs from web RA should have metadata['source'] == 'web')
        web_srcs   = [s for s in sources 
                      if s.get("metadata", {}).get("source") == "web"]
        local_srcs = [s for s in sources if s not in web_srcs]
        confidence = _calc_confidence(sources, plan, bool(web_docs))

        if not all_docs:
            return SynthesisOutput(
                answer=(
                    "No relevant legal provisions were found for your query. "
                    "Please try rephrasing or adding more detail."
                ),
                confidence=0.0,
                conflict_report=conflict_report,
            )

        if self.llm:
            answer, used_llm = self._llm_answer(
                plan.original_query, all_docs, local_graph,
                conflict_report, plan.intent,
            )
        else:
            answer   = self._rule_based_answer(
                plan.original_query, sources, local_graph,
                conflict_report, plan.intent,
            )
            used_llm = False

        logger.info(
            "SynthesisAgent | intent=%s docs=%d web=%d llm=%s confidence=%.2f",
            plan.intent, len(all_docs), len(web_docs), used_llm, confidence,
        )
        return SynthesisOutput(
            answer=answer,
            sources=local_srcs,
            graph_references=local_graph,
            web_sources=web_srcs,
            conflict_report=conflict_report,
            confidence=confidence,
            used_llm=used_llm,
        )

    # ── LLM path ──────────────────────────────────────────────────────────────

    def _llm_answer(
        self,
        query:           str,
        docs:            List[Dict],
        graph:           List[Dict],
        conflict_report: ConflictReport,
        intent:          str,
    ):
        ctx      = _build_context(docs, graph, conflict_report)
        template = _PROMPTS.get(intent, _PROMPTS["general"])
        prompt   = template.format(question=query, context=ctx)
        try:
            logger.info("SynthesisAgent | Calling LLM (max_tokens=1500, temp=0.3)...")
            t_start = time.perf_counter()
            answer = self.llm.generate(prompt, max_tokens=1500, temperature=0.3)
            t_elapsed = time.perf_counter() - t_start
            logger.info("SynthesisAgent | LLM response received in %.2fs", t_elapsed)
            
            if answer:
                if conflict_report and conflict_report.has_conflicts:
                    answer += f"\n\n---\n{conflict_report.summary}"
                return answer, True
        except Exception as e:
            logger.warning("LLM synthesis failed (%s) — rule-based fallback", e)
        return self._rule_based_answer(
            query, _build_sources(docs), graph, conflict_report, intent
        ), False

    # ── rule-based fallback ───────────────────────────────────────────────────

    def _rule_based_answer(
        self,
        query:           str,
        sources:         List[Dict],
        graph:           List[Dict],
        conflict_report: ConflictReport,
        intent:          str,
    ) -> str:
        if not sources:
            return "No relevant legal provisions found for your query."

        top  = sources[0]
        meta = top.get("metadata", {})
        act  = meta.get("act", meta.get("source", "legal documents"))
        sec  = f", Section {meta['section']}" if meta.get("section") else ""
        url_note = f"\n*(Source: {meta['url']})*" if meta.get("url") else ""

        if intent == "procedural":
            ans = f"**Procedure** ({act}{sec}):\n\n{top['excerpt']}{url_note}"
            if len(sources) > 1:
                ans += f"\n\n*{len(sources)-1} additional provision(s) may apply.*"

        elif intent == "comparative":
            ans = "**Comparison based on available provisions:**\n\n"
            for i, s in enumerate(sources[:4], 1):
                m   = s.get("metadata", {})
                lbl = f"{m.get('act','?')} s.{m.get('section','?')}"
                u   = f" ([link]({m['url']}))" if m.get("url") else ""
                ans += f"**{i}. {lbl}{u}**\n{s['excerpt']}\n\n"

        elif intent in ("case_law", "recent"):
            ans = f"**Result** (from {act}):\n\n{top['excerpt']}{url_note}"
            if len(sources) > 1:
                ans += "\n\n**Additional References:**\n"
                for s in sources[1:4]:
                    m   = s.get("metadata", {})
                    lbl = m.get("title") or m.get("act") or "Source"
                    u   = m.get("url", "")
                    ans += f"• [{lbl}]({u})\n" if u else f"• {lbl}\n"

        elif intent == "exploratory":
            ans = f"**Overview ({len(sources)} provisions found):**\n\n"
            for i, s in enumerate(sources[:5], 1):
                m   = s.get("metadata", {})
                lbl = f"{m.get('act','?')} s.{m.get('section','?')}"
                u   = f" ([link]({m['url']}))" if m.get("url") else ""
                ans += f"**{i}. {lbl}{u}**\n{s['excerpt']}\n\n"

        else:
            ans = f"According to {act}{sec}:\n\n{top['excerpt']}{url_note}"
            if len(sources) > 1:
                ans += f"\n\n*{len(sources)-1} other provision(s) also relevant.*"

        # case law footnote from graph
        cases = [f for f in graph if f.get("case_name")]
        if cases:
            ans += "\n\n**Related Case Law:**\n"
            for f in cases[:3]:
                ans += f"• {f['case_name']} ({f.get('case_year','')})\n"

        # conflict note
        if conflict_report and conflict_report.has_conflicts:
            ans += f"\n\n---\n{conflict_report.summary}"

        return ans


# ── module helpers ────────────────────────────────────────────────────────────

def _merge_and_rank(local: List[Dict], web: List[Dict]) -> List[Dict]:
    seen, merged = set(), []
    for d in local:
        uid = d.get("id", "")
        if uid not in seen:
            seen.add(uid)
            merged.append(d)
    for d in web:
        uid = d.get("id", "")
        if uid not in seen:
            seen.add(uid)
            merged.append(d)
    merged.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return merged


def _build_sources(docs: List[Dict]) -> List[Dict]:
    out = []
    for i, d in enumerate(docs, 1):
        content = d.get("content") or d.get("excerpt") or ""
        out.append({
            "id":              d.get("id", f"doc_{i}"),
            "content":         content,
            "excerpt":         content[:300] + ("..." if len(content) > 300 else ""),
            "relevance_score": d.get("relevance_score", 0.0),
            "metadata":        d.get("metadata", {}),
            "rank":            i,
        })
    return out


def _build_context(
    docs:            List[Dict],
    graph:           List[Dict],
    conflict_report: ConflictReport,
) -> str:
    # Filter out noise docs that are likely irrelevant
    filtered_docs = [d for d in docs if d.get("relevance_score", 0) >= RELEVANCE_FILTER_THRESHOLD]
    
    # Safety: if everything was filtered out, keep at least the top document to avoid empty context
    if not filtered_docs and docs:
        filtered_docs = [docs[0]]
        
    parts = []
    for i, d in enumerate(filtered_docs[:7], 1):
        meta  = d.get("metadata", {})
        act   = meta.get("act", meta.get("source", ""))
        sec   = meta.get("section", "")
        url   = meta.get("url", "")
        label = (f"[Doc {i}: {act} s.{sec}]" if act and sec
                 else f"[Doc {i}: {meta.get('source','?')}]")
        if url:
            label += f" {url}"
        text  = (d.get("content") or d.get("excerpt") or "")[:MAX_CTX_CHARS]
        parts.append(f"{label}\n{text}")
    
    
    if graph:
        parts.append("\n[Graph References]")
        for f in graph[:4]:
            if f.get("case_name"):
                parts.append(
                    f"• {f['case_name']} ({f.get('case_year','')}) "
                    f"— s.{f.get('section','')}"
                )
    if conflict_report and conflict_report.has_conflicts:
        parts.append(f"\n[Detected Conflicts]\n{conflict_report.summary}")
    return "\n\n".join(parts)


def _calc_confidence(sources: List[Dict], plan: Plan,
                     has_web: bool) -> float:
    if not sources:
        return 0.0
    top   = sources[0].get("relevance_score", 0.0)
    boost = min(0.05 * len(plan.sub_tasks), 0.15)
    web_b = 0.05 if has_web else 0.0
    return round(min(top + boost + web_b, 0.99), 4)
