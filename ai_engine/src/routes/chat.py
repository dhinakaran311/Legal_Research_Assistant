"""
Chat Routes — conversational legal research API
POST /api/chat              — send a message in a session
GET  /api/chat/{session_id}/history  — get session history
DELETE /api/chat/{session_id}        — clear session
GET  /api/chat/sessions              — list active sessions
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from middleware.api_key_middleware import require_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # if None, a new session is created
    use_llm: bool = True
    use_crew: bool = False              # use CrewAI crew instead of LangGraph


class ChatResponse(BaseModel):
    session_id: str
    question: str
    resolved_query: str
    intent: str
    intent_confidence: float
    answer: str
    sources: list
    graph_references: list
    web_sources: list
    num_sources_retrieved: int
    confidence: float
    processing_time_ms: float
    metadata: dict


class HistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: float
    metadata: dict


# ── Dependency: get conversation graph ───────────────────────────────────────

def get_conversation_graph():
    """Returns the singleton ConversationGraph from app state."""
    from pipeline_factory import get_conversation_graph as _get
    return _get()


def get_crew():
    """Returns the singleton LegalResearchCrew from app state."""
    from pipeline_factory import get_crew as _get
    return _get()


def get_memory():
    """Returns the singleton ConversationMemory."""
    from conversation.memory import get_memory as _get
    return _get()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(require_api_key)],
)
async def chat(request: ChatRequest):
    """
    Send a message and get a conversational legal research response.
    Creates a new session if session_id is not provided.
    """
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        "Chat request | session=%s message='%s' use_crew=%s",
        session_id[:8], request.message[:60], request.use_crew,
    )

    try:
        if request.use_crew:
            result = await _run_crew(request.message, session_id, request.use_llm)
        else:
            graph = get_conversation_graph()
            result = await graph.run_async(
                query=request.message,
                session_id=session_id,
                use_llm=request.use_llm,
            )

        return ChatResponse(
            session_id=session_id,
            question=result.get("question", request.message),
            resolved_query=result.get("resolved_query", request.message),
            intent=result.get("intent", "unknown"),
            intent_confidence=result.get("intent_confidence", 0.7),
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            graph_references=result.get("graph_references", []),
            web_sources=result.get("web_sources", []),
            num_sources_retrieved=result.get("num_sources_retrieved", 0),
            confidence=result.get("confidence", 0.0),
            processing_time_ms=result.get("processing_time_ms", 0.0),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        logger.error("Chat endpoint error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# NOTE: /sessions must be declared BEFORE /{session_id} to avoid route conflict
@router.get(
    "/chat/sessions",
    dependencies=[Depends(require_api_key)],
)
def list_sessions():
    """List all active session IDs."""
    memory = get_memory()
    sessions = memory.list_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@router.get(
    "/chat/{session_id}/history",
    dependencies=[Depends(require_api_key)],
)
def get_history(session_id: str):
    """Get conversation history for a session."""
    memory = get_memory()
    turns = memory.get_history(session_id)
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": t.role,
                "content": t.content,
                "timestamp": t.timestamp,
                "metadata": t.metadata,
            }
            for t in turns
        ],
        "total": len(turns),
    }


@router.delete(
    "/chat/{session_id}",
    dependencies=[Depends(require_api_key)],
)
def clear_session(session_id: str):
    """Clear a conversation session."""
    memory = get_memory()
    memory.clear_session(session_id)
    logger.info("Session cleared: %s", session_id)
    return {"success": True, "session_id": session_id}


@router.post(
    "/chat/stream",
    dependencies=[Depends(require_api_key)],
)
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint — returns Server-Sent Events.
    Streams the answer token by token using Groq streaming.
    """
    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        try:
            import json
            import os
            from groq import Groq
            from conversation.memory import get_memory as _get_mem
            from conversation.query_resolver import QueryResolver
            from agents.planner_agent import PlannerAgent
            from agents.local_research_agent import LocalResearchAgent
            from pipeline_factory import get_neo4j_client, get_chroma_client
            from llm.base import get_llm

            memory = _get_mem()
            llm = get_llm()

            # Save user message
            memory.add_turn(session_id=session_id, role="user", content=request.message)

            # Resolve query with history
            history = memory.get_history(session_id, last_n=4)
            resolver = QueryResolver(llm=llm)
            resolved = resolver.resolve(request.message, history[:-1])  # exclude current

            # Quick local search for context
            planner = PlannerAgent(llm=llm)
            plan = planner.plan(resolved)
            local_ra = LocalResearchAgent(
                chroma_client=get_chroma_client(),
                neo4j_client=get_neo4j_client(),
            )
            local_bundle = local_ra.research(plan)
            docs = local_bundle.all_documents[:5]

            # Build context
            context_parts = []
            for i, doc in enumerate(docs, 1):
                meta = doc.get("metadata", {})
                act = meta.get("act", "")
                sec = meta.get("section", "")
                label = f"[{act} s.{sec}]" if act and sec else f"[Doc {i}]"
                context_parts.append(f"{label}\n{doc.get('content','')[:600]}")
            context = "\n\n".join(context_parts) or "No local documents found."

            # Build history messages for Groq
            history_msgs = memory.get_llm_messages(session_id, last_n=4)
            # Remove the last user message (we'll add it with context)
            history_msgs = [m for m in history_msgs if not (
                m["role"] == "user" and m["content"] == request.message
            )]

            system_prompt = (
                "You are an expert Indian legal research assistant. "
                "Answer questions accurately using the provided legal documents. "
                "Always cite act names and section numbers. "
                "Be conversational and remember the context of our discussion."
            )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history_msgs)
            messages.append({
                "role": "user",
                "content": (
                    f"Legal Context:\n{context}\n\n"
                    f"Question: {resolved}"
                ),
            })

            # Stream from Groq
            groq_key = os.getenv("GROQ_API_KEY", "")
            groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            client = Groq(api_key=groq_key)

            full_answer = ""
            stream = client.chat.completions.create(
                model=groq_model,
                messages=messages,
                max_tokens=1024,
                temperature=0.3,
                stream=True,
            )

            # Send session_id first
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_answer += delta
                    yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"

            # Save assistant response to memory
            memory.add_turn(
                session_id=session_id,
                role="assistant",
                content=full_answer,
                metadata={"intent": plan.intent, "streamed": True},
            )

            # Send done signal with metadata
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'intent': plan.intent})}\n\n"

        except Exception as e:
            logger.error("Stream error: %s", e, exc_info=True)
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Crew helper ───────────────────────────────────────────────────────────────

async def _run_crew(message: str, session_id: str, use_llm: bool) -> dict:
    """Run LegalResearchCrew and wrap result in standard response shape."""
    import asyncio
    crew = get_crew()
    if not crew or not crew.available:
        # Fall back to ConversationGraph
        graph = get_conversation_graph()
        return await graph.run_async(query=message, session_id=session_id, use_llm=use_llm)

    # Crew is sync — run in thread pool
    from agents.planner_agent import PlannerAgent
    from llm.base import get_llm
    llm = get_llm()
    planner = PlannerAgent(llm=llm)
    plan = planner.plan(message)

    loop = asyncio.get_event_loop()
    crew_result = await loop.run_in_executor(
        None,
        lambda: crew.run(
            query=message,
            intent=plan.intent,
            needs_web=plan.use_web,
            needs_conflict_check=plan.needs_conflict_check,
        ),
    )

    return {
        "question": message,
        "resolved_query": message,
        "intent": plan.intent,
        "intent_confidence": 0.75,
        "answer": crew_result.get("answer", ""),
        "sources": [],
        "graph_references": [],
        "web_sources": [],
        "num_sources_retrieved": 0,
        "confidence": 0.75,
        "processing_time_ms": 0.0,
        "metadata": {"used_crew": True, "model": crew_result.get("model", "")},
    }
