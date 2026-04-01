"""
Agent 4 — ConflictCheckerAgent
────────────────────────────────
Compares documents across different Acts and flags:
  • CONTRADICTION  — opposing positions (bailable vs non-bailable, etc.)
  • OVERLAP        — both Acts address the same subject
  • AMBIGUITY      — unclear which provision applies

Uses LLM when available; keyword heuristics as fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Conflict:
    type:        str   # "contradiction" | "overlap" | "ambiguity"
    act_a:       str
    act_b:       str
    description: str
    resolution:  str = ""


@dataclass
class ConflictReport:
    conflicts:     List[Conflict] = field(default_factory=list)
    summary:       str  = ""
    has_conflicts: bool = False


class ConflictCheckerAgent:
    """Pairwise conflict detection across Acts in the document set."""

    def __init__(self, llm=None):
        self.llm = llm

    # ── public API ────────────────────────────────────────────────────────────

    def check(self, query: str,
              documents: List[Dict[str, Any]]) -> ConflictReport:
        # Filter out noise docs — use same threshold as SynthesisAgent
        relevant_docs = [d for d in documents if d.get("relevance_score", 0) >= 0.40]
        
        if not relevant_docs or len(relevant_docs) < 2:
            return ConflictReport()

        act_groups = self._group_by_act(relevant_docs)
        if len(act_groups) < 2:
            return ConflictReport()

        names     = list(act_groups.keys())
        conflicts = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                c = self._compare_pair(
                    query,
                    names[i], act_groups[names[i]],
                    names[j], act_groups[names[j]],
                )
                if c:
                    conflicts.append(c)

        if not conflicts:
            return ConflictReport()

        return ConflictReport(
            conflicts=conflicts,
            summary=self._summarise(conflicts),
            has_conflicts=True,
        )

    # ── private ───────────────────────────────────────────────────────────────

    def _group_by_act(self, docs: List[Dict]) -> Dict[str, List[Dict]]:
        groups: Dict[str, List[Dict]] = {}
        for d in docs:
            act = d.get("metadata", {}).get("act", "Unknown")
            if act and act != "Unknown":
                groups.setdefault(act, []).append(d)
        return groups

    def _compare_pair(
        self,
        query: str,
        act_a: str, docs_a: List[Dict],
        act_b: str, docs_b: List[Dict],
    ) -> Optional[Conflict]:
        text_a = " ".join(d.get("excerpt", "") for d in docs_a[:2])
        text_b = " ".join(d.get("excerpt", "") for d in docs_b[:2])
        if self.llm:
            return self._llm_compare(query, act_a, text_a, act_b, text_b)
        return self._heuristic_compare(act_a, text_a, act_b, text_b)

    def _llm_compare(self, query: str,
                     act_a: str, text_a: str,
                     act_b: str, text_b: str) -> Optional[Conflict]:
        prompt = (
            f"You are an Indian legal expert.\n"
            f"Compare these two excerpts for: {query}\n\n"
            f"{act_a}:\n{text_a[:600]}\n\n"
            f"{act_b}:\n{text_b[:600]}\n\n"
            "If there is a genuine conflict respond:\n"
            "TYPE: contradiction|overlap|ambiguity\n"
            "DESCRIPTION: <one sentence>\n"
            "RESOLUTION: <how to resolve>\n"
            "If NO conflict: respond NONE"
        )
        try:
            raw = self.llm.generate(prompt, max_tokens=150, temperature=0.2)
            if "NONE" in raw.upper():
                return None
            kv = {
                ln.split(":", 1)[0].strip().upper(): ln.split(":", 1)[1].strip()
                for ln in raw.splitlines() if ":" in ln
            }
            return Conflict(
                type=kv.get("TYPE", "overlap").lower(),
                act_a=act_a, act_b=act_b,
                description=kv.get("DESCRIPTION",
                                   f"Potential conflict between {act_a} and {act_b}"),
                resolution=kv.get("RESOLUTION", "Consult legal counsel."),
            )
        except Exception as e:
            logger.debug("LLM conflict check failed: %s", e)
            return self._heuristic_compare(act_a, text_a, act_b, text_b)

    def _heuristic_compare(self, act_a: str, text_a: str,
                           act_b: str, text_b: str) -> Optional[Conflict]:
        CONTRADICTIONS = [
            ("bailable",     "non-bailable"),
            ("cognizable",   "non-cognizable"),
            ("compoundable", "non-compoundable"),
            ("void",         "valid"),
            ("punishable",   "not punishable"),
        ]
        combined = (text_a + " " + text_b).lower()
        for pos, neg in CONTRADICTIONS:
            if pos in combined and neg in combined:
                return Conflict(
                    type="contradiction",
                    act_a=act_a, act_b=act_b,
                    description=(
                        f"{act_a} and {act_b} take opposing positions "
                        f"({pos!r} vs {neg!r})."
                    ),
                    resolution=(
                        "The special/later Act typically overrides the general Act. "
                        "Consult legal counsel."
                    ),
                )
        OVERLAPS = ["bail", "arrest", "penalty", "punishment", "fine",
                    "compensation", "damages"]
        for trigger in OVERLAPS:
            if trigger in text_a.lower() and trigger in text_b.lower():
                return Conflict(
                    type="overlap",
                    act_a=act_a, act_b=act_b,
                    description=(
                        f"Both {act_a} and {act_b} address '{trigger}'."
                    ),
                    resolution=(
                        "Apply the provision most specific to the facts. "
                        "A later or special Act may prevail."
                    ),
                )
        return None

    def _summarise(self, conflicts: List[Conflict]) -> str:
        lines = [f"⚠  {len(conflicts)} conflict(s) detected:"]
        for c in conflicts:
            lines.append(
                f"  • [{c.type.upper()}] {c.act_a} vs {c.act_b}: {c.description}"
            )
            if c.resolution:
                lines.append(f"    → Resolution: {c.resolution}")
        return "\n".join(lines)
