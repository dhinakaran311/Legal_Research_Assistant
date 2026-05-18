"""
Query Resolver
Resolves pronouns and references in user queries using conversation history.
Example: "what about its punishment?" + history → "what is the punishment under IPC Section 302?"
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from conversation.memory import ChatTurn

logger = logging.getLogger(__name__)

# Pronouns that indicate reference to previous context
REFERENCE_PATTERNS = [
    r'\b(it|its|that|this|these|those|them|they)\b',
    r'\b(what about|how about|tell me more|more info|explain)\b',
    r'^(and|also|additionally|furthermore)\b',
]


class QueryResolver:
    """
    Resolves ambiguous queries using conversation history.
    Uses fast Groq model (llama-3.1-8b-instant) for resolution.
    """

    def __init__(self, llm=None):
        self.llm = llm

    def needs_resolution(self, query: str) -> bool:
        """Check if query contains references that need resolution."""
        query_lower = query.lower()
        return any(re.search(pattern, query_lower, re.IGNORECASE)
                   for pattern in REFERENCE_PATTERNS)

    def resolve(
        self,
        current_query: str,
        history: List[ChatTurn],
    ) -> str:
        """
        Resolve current query using conversation history.
        Returns the resolved query (self-contained).
        """
        if not history:
            return current_query

        if not self.needs_resolution(current_query):
            logger.debug("Query doesn't need resolution")
            return current_query

        # Build context from last 3 turns
        context_turns = history[-6:]  # last 3 Q&A pairs
        context_text = "\n".join(
            f"{t.role.upper()}: {t.content[:200]}"
            for t in context_turns
        )

        if self.llm:
            return self._llm_resolve(current_query, context_text)
        else:
            return self._heuristic_resolve(current_query, context_turns)

    def _llm_resolve(self, query: str, context: str) -> str:
        """Use LLM to resolve query with context."""
        prompt = (
            "You are a query resolver for a legal research assistant.\n"
            "Given the conversation history and a new query, rewrite the query "
            "to be self-contained (no pronouns or references).\n\n"
            "RULES:\n"
            "- If the query is already clear, return it unchanged.\n"
            "- Replace pronouns (it, that, this) with the actual legal term from history.\n"
            "- Keep the query concise and natural.\n"
            "- Output ONLY the resolved query, nothing else.\n\n"
            f"CONVERSATION HISTORY:\n{context}\n\n"
            f"NEW QUERY: {query}\n\n"
            "RESOLVED QUERY:"
        )

        try:
            resolved = self.llm.generate(prompt, max_tokens=100, temperature=0.1)
            resolved = resolved.strip().strip('"').strip("'")
            logger.info("Query resolved: '%s' → '%s'", query[:50], resolved[:50])
            return resolved
        except Exception as e:
            logger.warning("LLM resolution failed: %s — using original", e)
            return query

    def _heuristic_resolve(self, query: str, history: List[ChatTurn]) -> str:
        """
        Fallback heuristic resolution without LLM.
        Extracts key entities from last assistant message.
        """
        if not history:
            return query

        # Get last assistant message
        last_assistant = None
        for turn in reversed(history):
            if turn.role == "assistant":
                last_assistant = turn.content
                break

        if not last_assistant:
            return query

        # Extract act/section mentions from last response
        act_match = re.search(
            r'\b(IPC|CrPC|CPC|Indian Penal Code|Evidence Act|Contract Act)\b',
            last_assistant,
            re.IGNORECASE
        )
        section_match = re.search(
            r'\b[Ss]ection\s+(\d+[A-Za-z]?)\b',
            last_assistant
        )

        # Replace pronouns with extracted entities
        resolved = query
        if act_match and section_match:
            act = act_match.group(1)
            section = section_match.group(1)
            resolved = re.sub(
                r'\b(it|its|that|this)\b',
                f"{act} Section {section}",
                resolved,
                flags=re.IGNORECASE
            )
        elif act_match:
            act = act_match.group(1)
            resolved = re.sub(
                r'\b(it|its|that|this)\b',
                act,
                resolved,
                flags=re.IGNORECASE
            )

        if resolved != query:
            logger.info("Heuristic resolution: '%s' → '%s'", query[:50], resolved[:50])

        return resolved
