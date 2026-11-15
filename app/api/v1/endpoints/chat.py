"""Chat endpoints for synchronous turns and real-time SSE streaming."""

from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.api.v1.schemas import ChatMessageRequest, ChatMessageResponse
from app.core.agent import get_chatbot, get_namebot
from app.core.db.repository import ThreadRepository

router = APIRouter(prefix="/chat", tags=["Chat"])


def _extract_text(content: Any) -> str:
    """Helper to reliably extract text from message content."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list) and len(content) > 0:
        first = content[0]
        if isinstance(first, dict):
            return first.get("text", "")
        return str(first)
    return ""


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Submit a message to the agent and receive the complete response synchronously.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    repo = ThreadRepository()
    bot = get_chatbot()

    try:
        response = bot.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
        ai_message = response["messages"][-1]
        text_content = _extract_text(ai_message.content)

        # Automated titling for new threads
        chat_name = repo.get_thread_name(thread_id)
        if not chat_name:
            namebot = get_namebot()
            name_resp = namebot.invoke(
                {"messages": [request.message, text_content]},
                config=config,
            )
            chat_name = name_resp.get("name", "New Chat")

        return ChatMessageResponse(
            role="assistant",
            content=text_content,
            thread_id=thread_id,
            thread_title=chat_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stream")
async def stream_chat_message(request: ChatMessageRequest):
    """
    Submit a message and stream tokens and tool status back as Server-Sent Events (SSE).
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    repo = ThreadRepository()
    bot = get_chatbot()

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response_text = ""
        try:
            # Emit thread assignment event
            yield f"data: {json.dumps({'event': 'init', 'thread_id': thread_id})}\n\n"

            for message_chunk, metadata in bot.stream(
                {"messages": [HumanMessage(content=request.message)]},
                stream_mode="messages",
                config=config,
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    yield f"data: {json.dumps({'event': 'tool_complete', 'tool': tool_name})}\n\n"

                elif isinstance(message_chunk, AIMessage):
                    # Check for tool call initialization
                    if getattr(message_chunk, "tool_calls", None):
                        for call in message_chunk.tool_calls:
                            yield f"data: {json.dumps({'event': 'tool_start', 'tool': call.get('name')})}\n\n"

                    chunk_text = _extract_text(message_chunk.content)
                    if chunk_text:
                        full_response_text += chunk_text
                        yield f"data: {json.dumps({'event': 'token', 'text': chunk_text})}\n\n"

            # Auto-title conversation if currently untitled
            chat_name = repo.get_thread_name(thread_id)
            if not chat_name:
                namebot = get_namebot()
                name_resp = namebot.invoke(
                    {"messages": [request.message, full_response_text]},
                    config=config,
                )
                chat_name = name_resp.get("name", "New Conversation")

            yield f"data: {json.dumps({'event': 'done', 'thread_id': thread_id, 'title': chat_name})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

