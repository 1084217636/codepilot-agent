"""OpenAI-compatible model construction, intentionally separate from graph wiring."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def build_chat_model() -> ChatOpenAI:
    """Create the configured OpenAI-compatible chat model for a real local run."""

    api_key = os.getenv("MODEL_API_KEY", "").strip()
    if not api_key:
        raise ValueError("MODEL_API_KEY is required; copy .env.example and configure a compatible provider")
    if api_key == "replace-me":
        raise ValueError("MODEL_API_KEY still has the example value; replace it with a real provider API key")
    return ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("MODEL_BASE_URL") or None,
        temperature=0,
    )
