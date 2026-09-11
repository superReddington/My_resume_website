from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agent.graph import get_graph, to_langchain_messages
from app.api.rate_limit import limiter
from app.core.config import settings
from app.db.pool import get_pool
import json
from collections.abc import AsyncIterator

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=80)
    message: str = Field(min_length=1, max_length=2000)


def _load_history(session_id: str) -> list[dict]:
    pool = get_pool()
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT messages FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        ).fetchone()
    if not row:
        return []
    return (row[0] or [])[-settings.max_history_messages :]


def _save_history(session_id: str, history: list[dict]) -> None:
    trimmed = history[-settings.max_history_messages :]
    payload = json.dumps(trimmed, ensure_ascii=False)
    pool = get_pool()
    with pool.connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_sessions (session_id, messages, updated_at)
            VALUES (%s, %s::jsonb, now())
            ON CONFLICT (session_id)
            DO UPDATE SET messages = EXCLUDED.messages, updated_at = now()
            """,
            (session_id, payload),
        )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chunk_text(chunk) -> str:
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text") or "")
        return "".join(parts)
    return ""


async def _stream_answer(session_id: str, message: str) -> AsyncIterator[str]:
    history = _load_history(session_id)
    graph = get_graph()
    lc_messages = to_langchain_messages(history)
    lc_messages.append(HumanMessage(content=message))
    collected: list[str] = []

    try:
        async for event in graph.astream_events(
            {"messages": lc_messages, "context": ""},
            version="v2",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                text = _chunk_text(event.get("data", {}).get("chunk"))
                if text:
                    collected.append(text)
                    yield _sse("token", {"content": text})
            elif kind == "on_tool_start":
                yield _sse("tool", {"name": event.get("name") or "search_knowledge"})

        answer = "".join(collected).strip()
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})
        _save_history(session_id, history)
        yield _sse("done", {"content": answer})
    except Exception as exc:
        yield _sse("error", {"message": str(exc)})


@router.post("/chat")
@limiter.limit(settings.chat_rate_limit)
async def chat(payload: ChatRequest, request: Request):
    return StreamingResponse(
        _stream_answer(payload.session_id, payload.message.strip()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
