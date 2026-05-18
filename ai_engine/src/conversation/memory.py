"""
Conversation Memory
Stores per-session message history in-memory with optional Redis persistence.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "10"))


@dataclass
class ChatTurn:
    role: str           # "user" | "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_llm_message(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class SessionMemory:
    session_id: str
    turns: List[ChatTurn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    title: Optional[str] = None  # auto-set from first user message


class ConversationMemory:
    """
    Thread-safe in-memory conversation store.
    Falls back gracefully if Redis is unavailable.
    """

    def __init__(self, use_redis: bool = True):
        self._sessions: Dict[str, SessionMemory] = {}
        self._lock = threading.Lock()
        self._redis = None

        if use_redis:
            self._try_connect_redis()

    def _try_connect_redis(self) -> None:
        try:
            import redis
            url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(url, socket_connect_timeout=2)
            r.ping()
            self._redis = r
            logger.info("ConversationMemory: Redis connected")
        except Exception as e:
            logger.info("ConversationMemory: Redis unavailable (%s) — using in-memory", e)

    # ── public API ────────────────────────────────────────────────────────────

    def get_or_create(self, session_id: str) -> SessionMemory:
        with self._lock:
            if session_id not in self._sessions:
                # Try loading from Redis first
                session = self._load_from_redis(session_id)
                if session is None:
                    session = SessionMemory(session_id=session_id)
                self._sessions[session_id] = session
            return self._sessions[session_id]

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ChatTurn:
        session = self.get_or_create(session_id)
        turn = ChatTurn(role=role, content=content, metadata=metadata or {})

        with self._lock:
            session.turns.append(turn)
            # Auto-title from first user message
            if role == "user" and session.title is None:
                session.title = content[:60] + ("..." if len(content) > 60 else "")
            # Keep only last N turns
            if len(session.turns) > MAX_HISTORY_TURNS * 2:
                session.turns = session.turns[-(MAX_HISTORY_TURNS * 2):]

        self._persist_to_redis(session)
        return turn

    def get_history(self, session_id: str, last_n: int = MAX_HISTORY_TURNS) -> List[ChatTurn]:
        session = self.get_or_create(session_id)
        return session.turns[-(last_n * 2):]

    def get_llm_messages(self, session_id: str, last_n: int = 6) -> List[dict]:
        """Returns history in OpenAI/Groq message format for LLM context."""
        turns = self.get_history(session_id, last_n)
        return [t.to_llm_message() for t in turns]

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
        if self._redis:
            try:
                self._redis.delete(f"chat:{session_id}")
            except Exception:
                pass

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())

    # ── Redis persistence ─────────────────────────────────────────────────────

    def _persist_to_redis(self, session: SessionMemory) -> None:
        if not self._redis:
            return
        try:
            data = {
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at,
                "turns": [asdict(t) for t in session.turns],
            }
            self._redis.setex(
                f"chat:{session.session_id}",
                86400,  # 24h TTL
                json.dumps(data),
            )
        except Exception as e:
            logger.warning("Redis persist failed: %s", e)

    def _load_from_redis(self, session_id: str) -> Optional[SessionMemory]:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(f"chat:{session_id}")
            if not raw:
                return None
            data = json.loads(raw)
            session = SessionMemory(
                session_id=data["session_id"],
                created_at=data.get("created_at", time.time()),
                title=data.get("title"),
            )
            session.turns = [ChatTurn(**t) for t in data.get("turns", [])]
            return session
        except Exception as e:
            logger.warning("Redis load failed: %s", e)
            return None


# ── singleton ─────────────────────────────────────────────────────────────────
_memory_instance: Optional[ConversationMemory] = None
_memory_lock = threading.Lock()


def get_memory() -> ConversationMemory:
    global _memory_instance
    if _memory_instance is not None:
        return _memory_instance
    with _memory_lock:
        if _memory_instance is None:
            _memory_instance = ConversationMemory()
    return _memory_instance
