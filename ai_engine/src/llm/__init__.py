"""
LLM Module
Handles LLM-based answer generation using Google Gemini
"""

from .gemini_generator import GeminiGenerator
from .prompts import LEGAL_PROMPTS

__all__ = ['GeminiGenerator', 'LEGAL_PROMPTS']
