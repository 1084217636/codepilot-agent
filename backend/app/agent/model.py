"""OpenAI-compatible model construction, intentionally separate from graph wiring."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def build_chat_model() -> ChatOpenAI:
    """Create the configured OpenAI-compatible chat model for a real local run."""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required; copy .env.example and configure a compatible provider")
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0,
    )
