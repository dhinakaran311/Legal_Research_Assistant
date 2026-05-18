"""
guardrails/legal_classifier.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIX #1 — Legal Domain Classifier

Determines whether a user query is related to Indian law before
any retrieval or LLM call is made.

Public API:
    is_legal_query(question: str) -> bool
    legal_confidence(question: str) -> float   (0.0 – 1.0)

Strategy (layered, fastest → slowest):
  Layer 1: Hard blocklist   — explicit non-legal signal → score 0.0
  Layer 2: Legal keywords   — positive Indian-law signal → score 0.3-1.0
  Layer 3: (optional) Embedding similarity — anchor-phrase cosine distance

Threshold: score >= LEGAL_THRESHOLD (default 0.35) → accepted as legal query.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ── Configurable threshold ────────────────────────────────────────────────────
# Queries scoring >= this value are treated as legal.
# Tune in config.py via LEGAL_CLASSIFIER_THRESHOLD.
_DEFAULT_THRESHOLD: float = 0.25  # Tuned: catches short legal queries like "IPC 302"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1 — HARD BLOCKLIST
# If ANY of these terms appear in the query it is immediately classified as
# NON-LEGAL and given a score of 0.0, regardless of other signals.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_NON_LEGAL_BLOCKLIST: List[str] = [
    # ── Programming / CS ──────────────────────────────────────────────────────
    "python", "java", "javascript", "typescript", "c++", "c#", "golang",
    "rust lang", "kotlin", "swift code", "php code", "ruby on rails",
    "react", "angular", "vue.js", "nextjs", "node.js", "express.js",
    "django", "flask", "fastapi tutorial", "spring boot", "laravel",
    "html css", "tailwind", "bootstrap css",
    "algorithm", "algorithms", "data structure", "dsa", "leetcode",
    "hackerrank", "codeforces", "competitive programming",
    "merge sort", "bubble sort", "quick sort", "heap sort", "binary search",
    "linked list", "binary tree", "graph traversal", "bfs", "dfs",
    "dynamic programming", "recursion code", "pointer arithmetic",
    "sql query", "database schema", "mongodb", "postgresql", "mysql syntax",
    "machine learning", "deep learning", "neural network", "pytorch",
    "tensorflow", "keras", "scikit-learn", "pandas dataframe",
    "numpy array", "matplotlib",
    "docker container", "kubernetes", "devops", "ci/cd", "git commit",
    "write code", "write a program", "write a function", "write a script",
    "code for", "implement a", "create a function", "debug this code",
    "fix this error", "runtime error", "segmentation fault",
    "compile error", "syntax error",
    # ── Sports / Entertainment ────────────────────────────────────────────────
    "ipl", "cricket score", "cricket match", "world cup cricket",
    "fifa", "football match", "premier league", "la liga",
    "bollywood", "movie review", "box office", "ott platform",
    "netflix show", "amazon prime", "disney hotstar",
    "virat kohli", "sachin tendulkar", "ms dhoni", "rohit sharma",
    # ── General Knowledge / Non-Legal ─────────────────────────────────────────
    "recipe", "cooking", "how to cook", "food recipe",
    "travel guide", "tourist places", "best hotels",
    "stock market tips", "crypto", "bitcoin price", "nifty sensex",
    "math problem", "solve this equation", "calculus", "algebra problem",
    "physics problem", "chemistry formula",
    "translate", "translation of", "meaning in hindi", "meaning in tamil",
    "write an essay", "write a story", "write a poem",
    "health tips", "home remedy", "exercise routine",
    "astrology", "horoscope", "vastu shastra",
    "geography", "capital of", "population of",
    "history of world war", "american history",
]

# Pre-compile blocklist into lowercase set for O(1) sub-string matching
_BLOCKLIST_SET: List[str] = [term.lower() for term in _NON_LEGAL_BLOCKLIST]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2 — LEGAL KEYWORD SCORING
# Each keyword carries a weight. The final score is normalised to [0, 1].
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# (keyword_pattern, weight)
# Patterns are matched as word-boundary regex (\b) for precision.
_LEGAL_KEYWORDS: List[Tuple[str, float]] = [
    # ── Indian Acts / Codes (high weight) ────────────────────────────────────
    (r"\bipc\b", 1.0),
    (r"ipc\s*\d+", 1.0),           # catches "IPC 302", "IPC302"
    (r"ipc section\s*\d+", 1.0),
    (r"\bcrpc\b", 1.0),
    (r"crpc\s*\d+", 1.0),
    (r"\bcpc\b", 0.9),
    (r"\bbns\b", 1.0),           # Bharatiya Nyaya Sanhita
    (r"\bbnss\b", 1.0),          # Bharatiya Nagarik Suraksha Sanhita
    (r"\bbsa\b", 0.9),           # Bharatiya Sakshya Adhiniyam
    (r"\bindian penal code\b", 1.0),
    (r"\bcriminal procedure code\b", 1.0),
    (r"\bcivil procedure code\b", 1.0),
    (r"\bevidence act\b", 1.0),
    (r"\bmotor vehicles act\b", 0.9),
    (r"\binformation technology act\b", 0.9),
    (r"\bit act\b", 0.7),
    (r"\bprevention of corruption act\b", 1.0),
    (r"\bnarcotic drugs\b", 0.9),
    (r"\bndps act\b", 1.0),
    (r"\bpoco act\b", 1.0),
    (r"\bprotection of children\b", 0.9),
    (r"\barmed forces\b", 0.6),
    (r"\bcompanies act\b", 0.9),
    (r"\bincome tax act\b", 0.9),
    (r"\bgst\b", 0.7),
    (r"\bforeign exchange\b", 0.8),
    (r"\bfema\b", 0.9),
    (r"\bpmla\b", 1.0),          # Prevention of Money Laundering Act
    (r"\bmoney laundering\b", 0.9),
    (r"\binsolvency\b", 0.8),
    (r"\bcontract act\b", 0.9),
    (r"\bnegotiable instruments act\b", 0.9),
    (r"\bconsumer protection act\b", 0.9),
    (r"\brtI\b", 0.7),
    (r"\bright to information\b", 0.8),
    (r"\bdomestic violence act\b", 1.0),
    (r"\bdowry prohibition\b", 1.0),
    (r"\bsc st act\b", 1.0),
    (r"\batrocities act\b", 0.9),
    (r"\bjuvenile justice\b", 0.9),

    # ── Constitutional Law ────────────────────────────────────────────────────
    (r"\bconstitution of india\b", 1.0),
    (r"\bfundamental right", 1.0),
    (r"\bdirective principle", 0.9),
    (r"\barticle \d+", 0.9),
    (r"\bwrit petition\b", 1.0),
    (r"\bhabeas corpus\b", 1.0),
    (r"\bmandamus\b", 1.0),
    (r"\bpil\b", 0.9),            # Public Interest Litigation
    (r"\bpublic interest litigation\b", 1.0),
    (r"\bsupreme court\b", 0.9),
    (r"\bhigh court\b", 0.9),
    (r"\bdistrict court\b", 0.8),
    (r"\bsessions court\b", 0.9),
    (r"\bmagistrate\b", 0.9),

    # ── Criminal Law ─────────────────────────────────────────────────────────
    (r"\bfir\b", 0.9),
    (r"\bfirst information report\b", 1.0),
    (r"\bbail\b", 0.9),
    (r"\banticipatory bail\b", 1.0),
    (r"\bremand\b", 0.9),
    (r"\bcustody\b", 0.8),
    (r"\bpolice custody\b", 1.0),
    (r"\bjudicial custody\b", 1.0),
    (r"\bcharge sheet\b", 0.9),
    (r"\bchargesheet\b", 0.9),
    (r"\barrest\b", 0.75),               # "can police arrest", "arrest without warrant"
    (r"\bwarrant\b", 0.8),               # "arrest without a warrant"
    (r"\bpolice arrest\b", 0.9),
    (r"\bpolice officer\b", 0.7),
    (r"\bpolice station\b", 0.7),
    (r"\bcognizable offence\b", 1.0),
    (r"\bnon-cognizable\b", 1.0),
    (r"\bbailable\b", 0.9),
    (r"\bnon-bailable\b", 1.0),
    (r"\bcompoundable\b", 0.9),
    (r"\bmurder\b", 0.8),
    (r"\bhomicide\b", 0.9),
    (r"\bculpable homicide\b", 1.0),
    (r"\brape\b", 0.9),
    (r"\bsexual assault\b", 0.9),
    (r"\btheft\b", 0.8),
    (r"\bdacoity\b", 1.0),
    (r"\bextortion\b", 0.8),
    (r"\bforgery\b", 0.8),
    (r"\bfraud\b", 0.7),
    (r"\bkidnapping\b", 0.8),
    (r"\babduction\b", 0.8),
    (r"\bcheating\b", 0.7),
    (r"\bsection \d+\b", 0.85),   # "section 302", "section 420" etc.
    (r"\bipc section\b", 1.0),
    (r"\bimprisonment\b", 0.9),
    (r"\bfine and imprisonment\b", 1.0),
    (r"\bpunishment for\b", 0.9),
    (r"\bpenalty for\b", 0.8),
    (r"\boffence\b", 0.8),
    (r"\boffender\b", 0.7),
    (r"\baccused\b", 0.8),
    (r"\bprosecution\b", 0.9),
    (r"\bconviction\b", 0.9),
    (r"\bacquittal\b", 1.0),
    (r"\bsentence\b", 0.7),
    (r"\bjudgment\b", 0.7),

    # ── Civil / Procedural Law ────────────────────────────────────────────────
    (r"\blawsuit\b", 0.8),
    (r"\bcivil suit\b", 0.9),
    (r"\bplaint\b", 0.9),
    (r"\bwritten statement\b", 0.8),
    (r"\bsummons\b", 0.9),
    (r"\binjunction\b", 0.9),
    (r"\bstay order\b", 0.9),
    (r"\bex parte\b", 0.9),
    (r"\binterlocutory\b", 1.0),
    (r"\bdecree\b", 0.9),
    (r"\bappeal\b", 0.7),
    (r"\brevision\b", 0.7),
    (r"\breview petition\b", 0.9),
    (r"\blimitation act\b", 0.9),

    # ── Legal Procedure & Terminology ─────────────────────────────────────────
    (r"\blegal notice\b", 0.9),
    (r"\bnotice period\b", 0.6),
    (r"\baffidavit\b", 0.9),
    (r"\bpetition\b", 0.7),
    (r"\badvocate\b", 0.8),
    (r"\blawyer\b", 0.7),
    (r"\blitigant\b", 0.9),
    (r"\bjurisdiction\b", 0.9),
    (r"\bcognizance\b", 1.0),
    (r"\bvenue of trial\b", 1.0),
    (r"\bwitness\b", 0.7),
    (r"\bevidence\b", 0.7),
    (r"\bcircumstantial evidence\b", 1.0),
    (r"\bhearsay\b", 0.9),
    (r"\bburden of proof\b", 1.0),
    (r"\bpresumption\b", 0.8),
    (r"\bconfession\b", 0.8),
    (r"\badmission\b", 0.6),
    (r"\bcross examination\b", 0.9),
    (r"\bexamination in chief\b", 1.0),
    (r"\bfile a case\b", 0.8),           # "how to file a case in court"
    (r"\bfile a complaint\b", 0.8),
    (r"\bcourt process\b", 0.8),
    (r"\bcourt procedure\b", 0.8),
    (r"\blegal case\b", 0.8),
    (r"\bcourt case\b", 0.8),
    (r"\blegal proceedings\b", 0.9),
    (r"\bunder indian law\b", 0.9),
    (r"\bindian law\b", 0.9),
    (r"\bunder law\b", 0.7),
    (r"\bin india.*law\b", 0.8),
    (r"\bin court\b", 0.7),              # "file a case in court"
    (r"\bgo to court\b", 0.8),
    (r"\bcriminal law\b", 0.9),
    (r"\bcivil law\b", 0.8),

    # ── Family / Personal Law ─────────────────────────────────────────────────
    (r"\bhma\b", 0.9),            # Hindu Marriage Act
    (r"\bhindu marriage act\b", 1.0),
    (r"\bdivorce\b", 0.8),
    (r"\bdivorce under\b", 0.9),
    (r"\bmatrimonial\b", 0.9),
    (r"\bmaintenance\b", 0.8),
    (r"\balimony\b", 0.9),
    (r"\bcustody of child\b", 0.9),
    (r"\bguardianship\b", 0.9),
    (r"\badoption\b", 0.7),
    (r"\bmuslim personal law\b", 1.0),
    (r"\btalaq\b", 1.0),
    (r"\bmeher\b", 1.0),
    (r"\bsuccession act\b", 0.9),
    (r"\binheritance law\b", 0.9),

    # ── Property / Land Law ───────────────────────────────────────────────────
    (r"\btransfer of property act\b", 1.0),
    (r"\bregistration act\b", 0.9),
    (r"\bstamp duty\b", 0.8),
    (r"\bease?ment\b", 0.9),
    (r"\bmortgage\b", 0.8),
    (r"\blease agreement\b", 0.7),
    (r"\btenant\b", 0.6),
    (r"\beviction\b", 0.8),
    (r"\bland acquisition\b", 0.9),
    (r"\bbenami\b", 1.0),

    # ── Scenario / Situation phrases (user describes a case without naming law) ───
    # These let users say "my landlord threw me out" and still get help.
    (r"\bwhat can i do\b", 0.5),          # "someone hit me, what can I do?"
    (r"\bwhat are my rights\b", 0.8),     # "what are my rights as a tenant?"
    (r"\bwhat legal\b", 0.7),             # "what legal action can I take?"
    (r"\blegal action\b", 0.8),
    (r"\blegal remedy\b", 0.9),
    (r"\blegal recourse\b", 0.9),
    (r"\blegal options\b", 0.8),
    (r"\bcan i sue\b", 0.9),
    (r"\bfile a complaint\b", 0.8),
    (r"\bfile an fir\b", 1.0),
    (r"\bmy rights\b", 0.6),
    (r"\bmy landlord\b", 0.6),            # landlord-tenant disputes
    (r"\bmy employer\b", 0.6),            # employment disputes
    (r"\bmy husband\b", 0.5),             # domestic / matrimonial
    (r"\bmy wife\b", 0.5),
    (r"\bmy boss\b", 0.5),
    (r"\bharrassing me\b", 0.6),
    (r"\bharassing me\b", 0.6),
    (r"\bthreatening me\b", 0.6),
    (r"\bassaulted me\b", 0.8),
    (r"\battacked me\b", 0.7),
    (r"\bstole my\b", 0.7),
    (r"\bcheated me\b", 0.7),
    (r"\bscammed me\b", 0.6),
    (r"\bfrauded me\b", 0.7),
    (r"\bfalsely accused\b", 0.8),
    (r"\bwrongfully arrested\b", 0.9),
    (r"\bunlawful detention\b", 0.9),
    (r"\bhit and run\b", 0.8),
    (r"\baccident case\b", 0.7),
    (r"\bwhat happens if\b", 0.4),        # "what happens if someone hits my car"
    (r"\bcan police\b", 0.7),             # "can police arrest without warrant?"
    (r"\bam i liable\b", 0.8),
    (r"\bpunishable\b", 0.8),
    (r"\bbreach of contract\b", 0.9),
    (r"\brefusal to pay\b", 0.7),
    (r"\bnot paid my salary\b", 0.7),
    (r"\bdomestic abuse\b", 0.9),
    (r"\bdomestic violence\b", 0.9),
    (r"\bsexual harassment\b", 0.9),
    (r"\bworkplace harassment\b", 0.8),
    (r"\bposh act\b", 0.9),
    (r"\bunfair dismissal\b", 0.8),
    (r"\bwrongful termination\b", 0.8),
    (r"\bcyber crime\b", 0.8),
    (r"\bonline fraud\b", 0.8),
    (r"\bscam\b", 0.6),                   # "I was scammed online"
    (r"\bget justice\b", 0.6),            # "how do I get justice?"
    (r"\blanded property\b", 0.7),
    (r"\bproperty dispute\b", 0.8),
    (r"\binheritance dispute\b", 0.8),
    (r"\bchild custody\b", 0.9),
    (r"\bseparation from spouse\b", 0.8),
    (r"\bwant justice\b", 0.5),
    (r"\bseek justice\b", 0.6),
    (r"\blegal help\b", 0.7),
    (r"\bneed legal\b", 0.7),
    (r"\blegal advice\b", 0.7),
]

# Pre-compile patterns once at module load time
_COMPILED_LEGAL_PATTERNS: List[Tuple[re.Pattern, float]] = [
    (re.compile(pattern, re.IGNORECASE), weight)
    for pattern, weight in _LEGAL_KEYWORDS
]

# Maximum possible raw score (sum of all weights) — used for normalisation
_MAX_RAW_SCORE: float = sum(w for _, w in _LEGAL_KEYWORDS)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def legal_confidence(question: str) -> float:
    """
    Return a confidence score in [0.0, 1.0] indicating how likely the
    question is an Indian law query.

    0.0  = clearly non-legal (blocklist hit)
    1.0  = clearly legal (many high-weight legal keywords)
    """
    if not question or not question.strip():
        return 0.0

    q_lower = question.lower()

    # ── Layer 1: blocklist ────────────────────────────────────────────────────
    for term in _BLOCKLIST_SET:
        if term in q_lower:
            logger.debug("Classifier: BLOCKLIST hit on '%s' in query '%s'",
                         term, question[:60])
            return 0.0

    # ── Layer 2: legal keyword scoring ────────────────────────────────────────
    raw_score: float = 0.0
    matched_keywords: List[str] = []

    for pattern, weight in _COMPILED_LEGAL_PATTERNS:
        if pattern.search(q_lower):
            raw_score += weight
            matched_keywords.append(pattern.pattern)

    # Normalise: use a soft cap so that 3+ solid matches → score ≥ 0.7
    # Formula: score = raw / (raw + SCALE), then apply floor of 0.2 if any match
    SCALE = 2.5
    if raw_score > 0:
        normalised = raw_score / (raw_score + SCALE)
        # Ensure at least one strong match gives meaningful score
        normalised = max(normalised, 0.25)
        logger.debug(
            "Classifier: raw=%.2f normalised=%.3f matched=%s query='%s'",
            raw_score, normalised, matched_keywords[:3], question[:60],
        )
        return round(min(normalised, 1.0), 4)

    # No keywords matched at all → very low score (might still be legal
    # if phrased generically, but we err on the side of rejection)
    logger.debug("Classifier: no legal keywords matched for query='%s'", question[:60])
    return 0.05


@lru_cache(maxsize=512)
def _cached_confidence(question: str) -> float:
    """LRU-cached wrapper around legal_confidence for repeated queries."""
    return legal_confidence(question)


def is_legal_query(question: str, threshold: float | None = None) -> bool:
    """
    Return True if the question is Indian-law related, False otherwise.

    Args:
        question:  The user's raw query string.
        threshold: Override the default confidence threshold (0.35).
                   Lower → more permissive; higher → stricter.

    Returns:
        bool — True means the pipeline should proceed; False means reject.
    """
    if threshold is None:
        # Try to read from settings; fall back to module default
        try:
            from config import settings
            threshold = getattr(settings, "LEGAL_CLASSIFIER_THRESHOLD", _DEFAULT_THRESHOLD)
        except Exception:
            threshold = _DEFAULT_THRESHOLD

    score = _cached_confidence(question)
    result = score >= threshold

    logger.info(
        "LegalClassifier | is_legal=%s score=%.3f threshold=%.2f query='%s'",
        result, score, threshold, question[:80],
    )
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFUSAL HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NON_LEGAL_REFUSAL = (
    "I am an Indian Legal Research Assistant and can only answer questions "
    "related to Indian law, legal procedures, acts, sections, and court "
    "judgments. Your question does not appear to be law-related. "
    "Please ask about topics such as IPC, CrPC, bail, FIR, constitutional "
    "rights, legal procedures, or specific Indian acts."
)
