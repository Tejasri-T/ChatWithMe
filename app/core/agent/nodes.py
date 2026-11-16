"""LangGraph execution nodes for chat handling and automated naming."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from app.core.agent.llm import get_llm
from app.core.agent.state import ChatState, NameSchema, NameState
from app.core.agent.tools import get_agent_tools
from app.core.db.repository import ThreadRepository


def chat_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
    """
    Primary chat node: constructs system instructions with thread context,
    binds available tools, and executes the LLM turn.
    """
    thread_id = None
    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    system_instruction = (
        "You are an enterprise AI assistant. For questions about uploaded documents, "
        f"call the `rag_tool` and explicitly include thread_id='{thread_id}'. "
        "You also have access to DuckDuckGo web search for real-time external information. "
        "Provide clear, factual, and well-structured responses. "
        "If a question requires document context but no PDF is available, ask the user to upload one."
    )

    llm = get_llm()
    tools = get_agent_tools()
    llm_with_tools = llm.bind_tools(tools)

    messages = [SystemMessage(content=system_instruction), *state["messages"]]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}


def name_node(state: NameState, config: RunnableConfig) -> dict[str, str]:
    """
    Automated titling node: analyzes initial conversation turns and generates
    a concise, non-colliding thread title.
    """
    repo = ThreadRepository()
    past_names = repo.get_all_thread_names()

    llm = get_llm()
    structured_llm = llm.with_structured_output(NameSchema)

    prompt = (
        f"Generate a concise 3-5 word title summarizing this conversation: {state['messages']}. "
        f"Do not reuse any of these existing titles: {past_names}."
    )

    response = structured_llm.invoke(prompt)
    chat_name = response.name if isinstance(response, NameSchema) else str(getattr(response, "name", "New Chat"))

    thread_id = "default"
    if config and isinstance(config, dict):
        thread_id = str(config.get("configurable", {}).get("thread_id", "default"))

    repo.upsert_thread(thread_id, chat_name)
    return {"name": chat_name}
