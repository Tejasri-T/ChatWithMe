"""Pydantic schemas for API request and response validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Payload for submitting a user message to the chatbot."""
    message: str = Field(..., min_length=1, description="User prompt text")
    thread_id: str | None = Field(None, description="Unique conversation thread identifier")


class ChatMessageResponse(BaseModel):
    """Synchronous chatbot turn response."""
    role: str = "assistant"
    content: str
    thread_id: str
    thread_title: str | None = None


class MessageItem(BaseModel):
    """Serialized message representation."""
    role: str
    content: str


class ThreadSummary(BaseModel):
    """High-level summary of a conversation thread."""
    thread_id: str
    chat_name: str


class ThreadDetailResponse(BaseModel):
    """Detailed view of a thread including message history and indexed document info."""
    thread_id: str
    chat_name: str | None = None
    messages: list[MessageItem]
    document_metadata: dict[str, Any] | None = None


class DocumentSummaryResponse(BaseModel):
    """Metadata response after document indexing."""
    filename: str
    documents: int
    chunks: int
    thread_id: str
    chunk_size: int
    chunk_overlap: int


class HealthResponse(BaseModel):
    """System health check payload."""
    status: str
    version: str
    environment: str
    database: str

