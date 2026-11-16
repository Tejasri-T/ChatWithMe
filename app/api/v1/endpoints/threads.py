"""Conversation thread management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.api.v1.schemas import MessageItem, ThreadDetailResponse, ThreadSummary
from app.core.agent import get_chatbot
from app.core.db.repository import ThreadRepository
from app.core.db.session import get_checkpointer
from app.core.rag import get_rag_service

router = APIRouter(prefix="/threads", tags=["Threads"])


def _serialize_message(msg) -> MessageItem:
    """Helper to convert LangChain messages to API schema items."""
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    content = ""
    if isinstance(msg.content, str):
        content = msg.content
    elif isinstance(msg.content, list) and len(msg.content) > 0:
        first = msg.content[0]
        content = first.get("text", "") if isinstance(first, dict) else str(first)
    return MessageItem(role=role, content=content)


@router.get("", response_model=list[ThreadSummary])
async def list_threads():
    """List all recorded conversation threads."""
    repo = ThreadRepository()
    checkpointer = get_checkpointer()

    try:
        # Collect thread IDs recorded in the checkpointer
        active_ids = {
            checkpoint.config["configurable"]["thread_id"]
            for checkpoint in checkpointer.list(None)
        }
        all_threads = repo.list_threads(list(active_ids) if active_ids else None)
        return [
            ThreadSummary(thread_id=tid, chat_name=name)
            for tid, name in all_threads.items()
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread_history(thread_id: str):
    """Retrieve full conversation history and attached document metadata for a thread."""
    bot = get_chatbot()
    repo = ThreadRepository()
    rag = get_rag_service()

    try:
        state = bot.get_state(config={"configurable": {"thread_id": thread_id}}).values
        raw_messages = state.get("messages", []) if state else []

        messages = [_serialize_message(m) for m in raw_messages if hasattr(m, "content")]
        chat_name = repo.get_thread_name(thread_id)
        doc_meta = rag.get_document_metadata(thread_id)

        return ThreadDetailResponse(
            thread_id=thread_id,
            chat_name=chat_name,
            messages=messages,
            document_metadata=doc_meta if doc_meta else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a conversation thread, its metadata, and in-memory document vectors."""
    repo = ThreadRepository()
    rag = get_rag_service()

    try:
        deleted = repo.delete_thread(thread_id)
        rag.delete_thread_documents(thread_id)
        return {"success": True, "thread_id": thread_id, "deleted": deleted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

