"""LangGraph workflow assembly and compilation."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.agent.nodes import chat_node, name_node
from app.core.agent.state import ChatState, NameState
from app.core.agent.tools import get_agent_tools
from app.core.db.session import get_checkpointer

_chatbot_app: Any = None
_namebot_app: Any = None


def build_chatbot(checkpointer: Any = None) -> Any:
    """Construct and compile the primary conversational state graph."""
    tools = get_agent_tools()
    tool_node = ToolNode(tools)

    workflow = StateGraph(ChatState)
    workflow.add_node("chat_node", chat_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "chat_node")
    workflow.add_conditional_edges("chat_node", tools_condition)
    workflow.add_edge("tools", "chat_node")

    cp = checkpointer or get_checkpointer()
    return workflow.compile(checkpointer=cp)


def build_namebot(checkpointer: Any = None) -> Any:
    """Construct and compile the automated conversation naming graph."""
    workflow = StateGraph(NameState)
    workflow.add_node("name_node", name_node)

    workflow.add_edge(START, "name_node")
    workflow.add_edge("name_node", END)

    cp = checkpointer or MemorySaver()
    return workflow.compile(checkpointer=cp)


def get_chatbot() -> Any:
    """Singleton accessor for the compiled chatbot application."""
    global _chatbot_app
    if _chatbot_app is None:
        _chatbot_app = build_chatbot()
    return _chatbot_app


def get_namebot() -> Any:
    """Singleton accessor for the compiled namebot application."""
    global _namebot_app
    if _namebot_app is None:
        _namebot_app = build_namebot()
    return _namebot_app

