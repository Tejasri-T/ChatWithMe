"""Embedding model factory and management."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings


@lru_cache()
def get_embeddings(api_key: Optional[str] = None) -> GoogleGenerativeAIEmbeddings:
    """
    Return a cached embedding model instance configured from settings.
    Raises ValueError if no API key is configured.
    """
    settings = get_settings()
    key = api_key or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if not key:
        raise ValueError(
            "GOOGLE_API_KEY is not configured. Please set GOOGLE_API_KEY in your .env file or environment."
        )

    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=key,
    )
