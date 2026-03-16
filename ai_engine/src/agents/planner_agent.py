"""
Agent 1 — PlannerAgent
─────────────────────
Analyses the user query and produces a structured Plan:
  • intent detection (keyword + optional LLM)
  • typed sub-tasks (STATUTE / CASE_LAW / PROCEDURE / COMPARISON / GENERAL)
  • routing flags  → use_local, use_web, needs_conflict_check
  • confidence_threshold → below this → escalate to web even for non-web intents
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── enums / data classes ──────────────────────────────────────────────────────

class TaskType(str, Enum):
    STATUTE    = "statute"
    CASE_LAW   = "case_law"
    PROCEDURE  = "procedure"
    COMPARISON = "comparison"
    GENERAL    = "general"


@dataclass
class SubTask:
    task_type:     TaskType
    query:         str
    section_hints: List[str] = field(default_factory=list)
    act_hints:     List[str] = field(default_factory=list)


@dataclass
class Plan:
    original_query:        str
    intent:                str
    sub_tasks:             List[SubTask] = field(default_factory=list)
    is_complex:            bool = False
    # routing
    use_local:             bool = True
    use_web:               bool = False   # forced web (intent-based)
    needs_conflict_check:  bool = False
    # set by pipeline after local search quality check
    escalate_to_web:       bool = False   # low-confidence fallback


# ── keyword maps ──────────────────────────────────────────────────────────────

_INTENT_KEYWORDS = {
    "comparative": ["difference between", "compare", "versus", "vs", "distinction",
                    "compare and contrast", "what is the difference"],
    "procedural":  ["how to", "how do i", "how can i", "procedure", "steps to",
                    "process of", "file", "apply for", "register", "obtain", "submit"],
    "factual":     ["punishment for", "penalty for", "sentence for",
                    "what is the punishment", "what is the penalty",
                    "what is the fine", "define", "section", "liable", "offence"],
    "exploratory": ["tell me about", "overview of", "explain", "all about",
                    "comprehensive", "detailed information", "everything about"],
    "case_law":    ["case", "judgment", "ruling", "precedent", "court decided",
                    "landmark", "supreme court", "high court", "tribunal"],
    "recent":      ["latest", "recent", "new law", "amendment", "2023", "2024",
                    "2025", "current", "updated", "notification", "circular",
                    "gazette", "ordinance"],
}

_ACT_KEYWORDS = {
    "IPC":      ["ipc", "indian penal code", "murder", "theft", "cheating",
                 "fraud", "assault", "robbery", "dacoity", "kidnapping", "rape",
                 "extortion", "forgery"],
    "CrPC":     ["crpc", "criminal procedure", "bail", "fir", "arrest",
                 "cognizable", "charge sheet", "remand", "anticipatory bail",
                 "summons", "warrant", "police"],
    "CPC":      ["cpc", "civil procedure", "suit", "plaint", "decree",
                 "injunction", "stay order", "appeal", "execution"],
    "Evidence": ["evidence act", "admissible", "confession", "witness",
                 "burden of proof", "hearsay", "expert opinion"],
    "Contract": ["contract act", "offer", "acceptance", "consideration",
                 "breach of contract", "void", "voidable", "indemnity",
                 "guarantee", "agency", "bailment"],
    "MVA":      ["motor vehicles", "driving license", "traffic", "accident",
                 "vehicle insurance", "hit and run", "drunk driving"],
    "ITA":      ["income tax", "section 80", "deduction", "tds", "assessment",
                 "advance tax", "return", "exemption"],
    "GST":      ["gst", "goods and services tax", "input credit", "igst",
                 "cgst", "sgst", "e-way bill", "invoice"],
    "RTI":      ["rti", "right to information", "public authority", "pio",
                 "information commission", "transparency"],
    "TPA":      ["transfer of property", "mortgage", "lease", "sale deed",
                 "easement", "gift deed", "exchange"],
    "HMA":      ["hindu marriage", "divorce", "matrimonial", "alimony",
                 "maintenance", "custody", "adoption"],
    "IT Act":   ["it act", "cyber", "hacking", "data breach", "phishing",
                 "information technology", "e-commerce", "digital signature",
                 "electronic evidence"],
    "Consumer": ["consumer protection", "consumer complaint", "deficiency",
                 "unfair trade", "misleading advertisement", "consumer forum"],
    "Labour":   ["labour law", "employment", "industrial dispute", "workman",
                 "wages", "minimum wages", "maternity", "provident fund",
                 "gratuity"],
    "NIA":      ["negotiable instruments", "cheque", "cheque bounce",
                 "dishonour", "section 138", "promissory note"],
}

# force web search for these keywords
_FORCE_WEB = [
    "latest", "recent", "new", "amendment", "2023", "2024", "2025",
    "current", "updated", "notification", "circular", "gazette",
    "supreme court", "high court", "judgment", "ruling", "verdict",
    "ordinance", "bill passed",
]

# trigger conflict checking
_CONFLICT_TRIGGERS = [
    "difference between", "compare", "versus", "conflict", "overlap",
    "both acts", "two laws", "contradiction", "which prevails",
    "which law applies",
]

_SECTION_RE = re.compile(
    r'\b(?:section|sec\.?|s\.)\s*(\d+[A-Za-z]?(?:\(\d+\))?)', re.IGNORECASE
)

# minimum local relevance score before escalating to web
LOCAL_CONFIDENCE_THRESHOLD = 0.40


# ── pure functions ────────────────────────────────────────────────────────────

def detect_intent_kw(query: str) -> str:
    q = query.lower()
    for intent, kws in _INTENT_KEYWORDS.items():
        if any(k in q for k in kws):
            return intent
    return "general"


def extract_acts(query: str) -> List[str]:
    q = query.lower()
    return [act for act, kws in _ACT_KEYWORDS.items()
            if any(k in q for k in kws)]


def extract_sections(query: str) -> List[str]:
    return [m.group(1) for m in _SECTION_RE.finditer(query)]


def should_force_web(query: str, intent: str) -> bool:
    q = query.lower()
    return (intent in ("case_law", "recent")
            or any(t in q for t in _FORCE_WEB))


def should_check_conflicts(query: str, intent: str) -> bool:
    q = query.lower()
    return (intent == "comparative"
            or any(t in q for t in _CONFLICT_TRIGGERS))


def build_sub_tasks(
    query: str,
    intent: str,
    acts: List[str],
    sections: List[str],
) -> List[SubTask]:
    tasks: List[SubTask] = []

    if intent == "comparative":
        tasks.append(SubTask(task_type=TaskType.COMPARISON, query=query,
                             act_hints=acts, section_hints=sections))
        for act in acts:
            tasks.append(SubTask(
                task_type=TaskType.STATUTE,
                query=f"{query} — focusing on {act}",
                act_hints=[act], section_hints=sections,
            ))

    elif intent == "procedural":
        tasks.append(SubTask(task_type=TaskType.PROCEDURE, query=query,
                             act_hints=acts, section_hints=sections))

    elif intent == "case_law":
        tasks.append(SubTask(task_type=TaskType.CASE_LAW, query=query,
                             act_hints=acts, section_hints=sections))

    else:
        tasks.append(SubTask(task_type=TaskType.STATUTE, query=query,
                             act_hints=acts, section_hints=sections))
        if sections:
            tasks.append(SubTask(task_type=TaskType.CASE_LAW, query=query,
                                 act_hints=acts, section_hints=sections))

    return tasks or [SubTask(task_type=TaskType.GENERAL, query=query)]


# ── agent class ───────────────────────────────────────────────────────────────

class PlannerAgent:
    """
    Stateless — call plan() for every query.
    Optionally uses LLM for intent detection; keyword rules are the fallback.
    """

    def __init__(self, llm=None):
        self.llm = llm

    def plan(self, query: str) -> Plan:
        intent   = self._detect_intent(query)
        acts     = extract_acts(query)
        sections = extract_sections(query)
        tasks    = build_sub_tasks(query, intent, acts, sections)

        force_web      = should_force_web(query, intent)
        needs_conflict = should_check_conflicts(query, intent)
        is_complex     = len(tasks) > 1 or force_web or needs_conflict

        logger.info(
            "PlannerAgent | intent=%-12s acts=%-20s sections=%s "
            "tasks=%d force_web=%s conflict=%s",
            intent, acts, sections, len(tasks), force_web, needs_conflict,
        )

        return Plan(
            original_query=query,
            intent=intent,
            sub_tasks=tasks,
            is_complex=is_complex,
            use_local=True,
            use_web=force_web,
            needs_conflict_check=needs_conflict,
            escalate_to_web=False,  # set later by pipeline
        )

    # ── private ───────────────────────────────────────────────────────────────

    def _detect_intent(self, query: str) -> str:
        if self.llm:
            prompt = (
                "Classify this Indian legal query into ONE word:\n"
                "factual | procedural | comparative | exploratory | "
                "case_law | recent | general\n\n"
                "GUIDELINES:\n"
                "- Use 'comparative' ONLY if comparing two different things or laws (e.g., 'A vs B').\n"
                "- Use 'factual' for 'what is the law/punishment for X'.\n\n"
                f"Query: {query}\nAnswer (one word only):"
            )
            try:
                raw = self.llm.generate(
                    prompt, max_tokens=5, temperature=0.0
                ).lower().strip()
                for intent in ("factual", "procedural", "comparative",
                               "exploratory", "case_law", "recent"):
                    if intent in raw:
                        return intent
            except Exception as e:
                logger.debug("LLM intent detection failed: %s", e)
        return detect_intent_kw(query)
