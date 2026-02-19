# app/core/llm.py
from __future__ import annotations

from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import settings


@lru_cache(maxsize=1)
def get_chat_model() -> ChatGoogleGenerativeAI:
    # LangChain: set GOOGLE_API_KEY env var (recommended) or pass api_key param :contentReference[oaicite:4]{index=4}
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=0.2,
        api_key=settings.effective_api_key,
    )


@lru_cache(maxsize=1)
def get_embedder() -> GoogleGenerativeAIEmbeddings:
    # LangChain embeddings: set GOOGLE_API_KEY env var or pass google_api_key kwarg :contentReference[oaicite:5]{index=5}
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embed_model,
        google_api_key=settings.effective_api_key,
    )
