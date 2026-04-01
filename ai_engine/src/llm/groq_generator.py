"""
Groq LLM Generator
Fast inference via Groq API (llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768)
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class GroqGenerator:
    """
    Groq API wrapper — uses the official `groq` SDK.
    Thread-safe lazy client init.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._client = None
        self._lock = threading.Lock()

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

        logger.info("GroqGenerator initialized | model=%s", self.model)

    def _get_client(self):
        with self._lock:
            if self._client is None:
                from groq import Groq
                self._client = Groq(api_key=self.api_key, timeout=self.timeout)
        return self._client

    def try_refresh(self) -> None:
        new_key = os.getenv("GROQ_API_KEY", self.api_key)
        with self._lock:
            self.api_key = new_key
            self._client = None
        logger.info("GroqGenerator: client refreshed")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Groq generation failed: %s", e)
            raise

    def generate_with_history(
        self,
        messages: list,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate with full message history for conversational context.
        messages: [{"role": "user"|"assistant", "content": str}, ...]
        """
        try:
            client = self._get_client()
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            response = client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Groq generate_with_history failed: %s", e)
            raise

    def is_available(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False


# ── singleton ─────────────────────────────────────────────────────────────────
_instance: Optional[GroqGenerator] = None
_lock = threading.Lock()


def get_groq_generator(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> GroqGenerator:
    global _instance
    if _instance is not None:
        return _instance
    with _lock:
        if _instance is None:
            _instance = GroqGenerator(
                api_key=api_key,
                model=model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            )
    return _instance
