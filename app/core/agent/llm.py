"""Centralized LLM model factory and configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings


@lru_cache()
def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
) -> ChatGoogleGenerativeAI:
    """
    Return a configured ChatGoogleGenerativeAI instance.
    Raises ValueError on invocation if no API key is supplied.
    """
    settings = get_settings()
    key = api_key or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    selected_model = model or settings.LLM_MODEL

    kwargs = {
        "model": selected_model,
        "temperature": temperature,
        "max_output_tokens": settings.MAX_TOKENS,
    }
    if key:
        kwargs["google_api_key"] = key

    return ChatGoogleGenerativeAI(**kwargs)

