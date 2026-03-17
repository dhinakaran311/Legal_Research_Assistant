"""
llm/base.py — LLM Provider Abstraction
────────────────────────────────────────
Single config change to swap providers.

Set LLM_PROVIDER in .env:
  ollama  → local Llama (default, free)
  gemini  → Google Gemini (needs GEMINI_API_KEY)
  openai  → OpenAI (needs OPENAI_API_KEY)
  none    → fully rule-based, no LLM at all

Usage:
    from llm.base import get_llm
    llm = get_llm()
    text = llm.generate("Your prompt here")
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# ── abstract base ─────────────────────────────────────────────────────────────

class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        prompt:      str,
        max_tokens:  int   = 500,
        temperature: float = 0.3,
    ) -> str:
        ...

    def is_available(self) -> bool:
        return True


# ── Ollama (local) ────────────────────────────────────────────────────────────

class OllamaLLM(BaseLLM):
    def __init__(
        self,
        model:    str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
    ):
        self.model    = model
        self.base_url = base_url

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.3) -> str:
        try:
            import requests
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model":   self.model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=300,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error("Ollama error: %s", e)
            raise

    def is_available(self) -> bool:
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False


# ── Google Gemini ─────────────────────────────────────────────────────────────

class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model   = model
        self._client = None

    def _get_client(self):
        if not self._client:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.3) -> str:
        try:
            import google.generativeai as genai
            client = self._get_client()
            config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            resp = client.generate_content(prompt, generation_config=config)
            return resp.text.strip()
        except Exception as e:
            logger.error("Gemini error: %s", e)
            raise


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model   = model
        self._client = None

    def _get_client(self):
        if not self._client:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.3) -> str:
        try:
            client = self._get_client()
            resp   = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("OpenAI error: %s", e)
            raise


# ── No-op (rule-based only) ───────────────────────────────────────────────────

class NoLLM(BaseLLM):
    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.3) -> str:
        raise RuntimeError("No LLM configured — rule-based mode")

    def is_available(self) -> bool:
        return False


# ── factory ───────────────────────────────────────────────────────────────────

def get_llm() -> BaseLLM:
    """
    Read LLM_PROVIDER from environment and return the right implementation.
    Falls back gracefully if keys are missing or providers unreachable.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

    if provider == "none":
        logger.info("LLM provider: none (rule-based fallback)")
        return NoLLM()

    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            logger.warning("GEMINI_API_KEY missing — falling back to rule-based")
            return NoLLM()
        logger.info("LLM provider: Gemini (%s)", os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        return GeminiLLM(
            api_key=key,
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        )

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            logger.warning("OPENAI_API_KEY missing — falling back to rule-based")
            return NoLLM()
        logger.info("LLM provider: OpenAI (%s)", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        return OpenAILLM(
            api_key=key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )

    # default: Ollama
    llm = OllamaLLM(
        model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    if llm.is_available():
        logger.info("LLM provider: Ollama (%s)", llm.model)
    else:
        logger.warning("Ollama not reachable — falling back to rule-based")
        return NoLLM()
    return llm
