"""
llm/base.py — LLM Provider Abstraction  (v2 — P0 fix)
────────────────────────────────────────────────────────
Changes vs v1
  • GeminiLLM now uses the NEW google-genai SDK (google.genai) instead of
    the deprecated google.generativeai SDK.
  • All providers have tenacity retry with exponential back-off on 429 / 503.
  • GeminiLLM.try_refresh() lets you hot-rotate the API key at runtime
    without restarting the service — just update GEMINI_API_KEY in the env
    and call try_refresh().
  • OllamaLLM timeout is now configurable via OLLAMA_TIMEOUT env var.

Set LLM_PROVIDER in .env:
  ollama  → local Llama (default, free)
  gemini  → Google Gemini (needs GEMINI_API_KEY)
  openai  → OpenAI (needs OPENAI_API_KEY)
  none    → fully rule-based, no LLM at all

Usage:
    from llm.base import get_llm
    llm = get_llm()
    text = llm.generate("Your prompt here")

    # Hot-rotate Gemini key without restart:
    import os; os.environ["GEMINI_API_KEY"] = "new-key"
    llm.try_refresh()
"""

from __future__ import annotations

import logging
import os
import threading
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

# ── tenacity retry (optional dep, degrades gracefully) ────────────────────────
try:
    import tenacity

    def _retry_decorator():
        """Exponential back-off: 1 s → 60 s, up to 3 attempts."""
        return tenacity.retry(
            wait=tenacity.wait_exponential(multiplier=1, min=1, max=60),
            stop=tenacity.stop_after_attempt(3),
            retry=tenacity.retry_if_exception_type((Exception,)),
            retry_error_callback=lambda rs: (_ for _ in ()).throw(rs.outcome.exception()),
            reraise=False,
        )

    _TENACITY_AVAILABLE = True
    logger.debug("tenacity available — retry logic enabled")
except ImportError:
    _TENACITY_AVAILABLE = False
    logger.warning("tenacity not installed — no automatic retry (pip install tenacity)")

    def _retry_decorator():
        """No-op fallback when tenacity is absent."""
        def _wrap(fn):
            return fn
        return _wrap


def _retryable(fn):
    """Apply retry decorator only for Gemini 429/503 errors."""
    if not _TENACITY_AVAILABLE:
        return fn

    import tenacity

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=60),
        stop=tenacity.stop_after_attempt(3),
        retry=tenacity.retry_if_exception(
            lambda e: _is_retryable_error(e)
        ),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def _is_retryable_error(exc: Exception) -> bool:
    """Return True for transient API errors worth retrying."""
    err_str = str(exc).lower()
    retryable_phrases = [
        "429", "quota", "resource exhausted",
        "503", "service unavailable", "overloaded",
        "rate limit", "too many requests",
    ]
    return any(p in err_str for p in retryable_phrases)


# ── abstract base ─────────────────────────────────────────────────────────────

class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        prompt:      str,
        max_tokens:  int   = 500,
        temperature: float = 0.1,    # FIX #5: deterministic grounded generation
        top_p:       float = 0.3,    # FIX #5: narrow nucleus — no open generation
    ) -> str:
        ...

    def is_available(self) -> bool:
        return True

    def try_refresh(self) -> None:
        """
        Hot-rotate credentials/connection.
        Subclasses that hold a client should reset it to None here so the
        next generate() call creates a fresh client with updated env vars.
        Default is a no-op (safe to call on any provider).
        """
        pass


# ── Ollama (local) ────────────────────────────────────────────────────────────

class OllamaLLM(BaseLLM):
    def __init__(
        self,
        model:    str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
    ):
        self.model    = model
        self.base_url = base_url
        self.timeout  = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.1,  # FIX #5
                 top_p: float = 0.3) -> str:
        return self._generate_inner(prompt, max_tokens, temperature, top_p)

    @_retryable
    def _generate_inner(self, prompt: str, max_tokens: int,
                        temperature: float, top_p: float = 0.3) -> str:
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
                        "top_p":       top_p,
                    },
                },
                timeout=self.timeout,
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


# ── Google Gemini (new google-genai SDK) ──────────────────────────────────────

class GeminiLLM(BaseLLM):
    """
    Uses the NEW google.genai SDK (google-genai >= 1.0.0).

    Key difference from old SDK
    ───────────────────────────
    Old (deprecated): import google.generativeai as genai
    New:              from google import genai
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._api_key = api_key
        self.model    = model
        self._client  = None          # lazy-loaded; reset by try_refresh()
        self._lock    = threading.Lock()

    def _get_client(self):
        """Thread-safe lazy initialisation of the Gemini client."""
        with self._lock:
            if self._client is None:
                from google import genai  # new SDK
                self._client = genai.Client(api_key=self._api_key)
        return self._client

    def try_refresh(self) -> None:
        """
        Hot-rotate the API key without restarting the service.

        Usage:
            import os
            os.environ["GEMINI_API_KEY"] = "new-key"
            llm.try_refresh()   # next generate() uses the new key
        """
        new_key = os.getenv("GEMINI_API_KEY", self._api_key)
        with self._lock:
            self._api_key = new_key
            self._client  = None          # force re-init on next call
        logger.info("GeminiLLM: client refreshed (key rotated)")

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.1,  # FIX #5
                 top_p: float = 0.3) -> str:
        return self._generate_inner(prompt, max_tokens, temperature, top_p)

    @_retryable
    def _generate_inner(self, prompt: str, max_tokens: int,
                        temperature: float, top_p: float = 0.3) -> str:
        try:
            from google.genai import types  # new SDK types
            client   = self._get_client()
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,      # FIX #5: narrow nucleus
                    top_k=10,         # FIX #5: also restrict top-k
                ),
            )
            if response and response.text:
                return response.text.strip()
            # Safety block or empty response
            fb = getattr(response, "prompt_feedback", None)
            raise RuntimeError(
                f"Gemini empty response (feedback={fb})"
            )
        except Exception as e:
            logger.error("Gemini error: %s", e)
            raise

    def is_available(self) -> bool:
        try:
            self._get_client()   # just checks connection; no API call
            return True
        except Exception:
            return False


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key  = api_key
        self.model    = model
        self._client  = None
        self._lock    = threading.Lock()

    def _get_client(self):
        with self._lock:
            if self._client is None:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
        return self._client

    def try_refresh(self) -> None:
        new_key = os.getenv("OPENAI_API_KEY", self.api_key)
        with self._lock:
            self.api_key = new_key
            self._client = None
        logger.info("OpenAILLM: client refreshed")

    def generate(self, prompt: str, max_tokens: int = 500,
                 temperature: float = 0.1,  # FIX #5
                 top_p: float = 0.3) -> str:
        return self._generate_inner(prompt, max_tokens, temperature, top_p)

    @_retryable
    def _generate_inner(self, prompt: str, max_tokens: int,
                        temperature: float, top_p: float = 0.3) -> str:
        try:
            client = self._get_client()
            resp   = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,  # FIX #5
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

_llm_instance: Optional[BaseLLM] = None
_llm_lock     = threading.Lock()


def get_llm(force_new: bool = False) -> BaseLLM:
    """
    Read LLM_PROVIDER from environment and return the right implementation.
    Returns a cached singleton unless force_new=True.
    Falls back gracefully if keys are missing or providers unreachable.

    Args:
        force_new: If True, discard cached instance and create a fresh one.
                   Use after calling try_refresh() on the old instance.
    """
    global _llm_instance

    with _llm_lock:
        if _llm_instance is not None and not force_new:
            return _llm_instance
        _llm_instance = _create_llm()
        return _llm_instance


def _create_llm() -> BaseLLM:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

    if provider == "none":
        logger.info("LLM provider: none (rule-based fallback)")
        return NoLLM()

    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            logger.warning("GEMINI_API_KEY missing — falling back to rule-based")
            return NoLLM()
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        logger.info("LLM provider: Gemini (%s)", model)
        return GeminiLLM(api_key=key, model=model)

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            logger.warning("OPENAI_API_KEY missing — falling back to rule-based")
            return NoLLM()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info("LLM provider: OpenAI (%s)", model)
        return OpenAILLM(api_key=key, model=model)

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
