"""State definitions and validation schemas for LangGraph workflows."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class ChatState(TypedDict):
    """Primary conversational state tracking message sequence."""
    messages: Annotated[list[BaseMessage], add_messages]


class NameState(TypedDict):
    """State for auto-generating conversation titles."""
    messages: list[Any]
    name: str


class NameSchema(BaseModel):
    """Pydantic schema enforcing structured title output from the LLM."""
    name: str = Field(
        description="A concise, descriptive 3-5 word title summarizing the chat topic"
    )

