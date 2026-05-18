"""
guardrails — Legal domain enforcement layer.

Exports:
  is_legal_query(question)  -> bool
  legal_confidence(question) -> float
"""
from guardrails.legal_classifier import is_legal_query, legal_confidence

__all__ = ["is_legal_query", "legal_confidence"]
