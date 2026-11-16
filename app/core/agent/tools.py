"""Tool registry and definitions for the conversational agent."""

from __future__ import annotations

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool, tool

from app.core.rag import get_rag_service


@tool
def rag_tool(query: str, thread_id: str | None = None) -> dict:
    """
    Retrieve relevant information from the uploaded PDF document.
    Use this tool when the user asks factual, conceptual, or specific questions about the stored documents.
    """
    rag_service = get_rag_service()
    return rag_service.retrieve_context(thread_id=thread_id, query=query)


def get_agent_tools() -> list[BaseTool]:
    """Return the suite of registered tools available to the chatbot."""
    search_tool = DuckDuckGoSearchRun()
    return [search_tool, rag_tool]

