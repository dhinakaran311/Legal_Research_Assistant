"""
LLM Module
Handles LLM-based answer generation
"""

from .ollama_generator import OllamaGenerator
from .prompts import LEGAL_PROMPTS

__all__ = ['OllamaGenerator', 'LEGAL_PROMPTS']
