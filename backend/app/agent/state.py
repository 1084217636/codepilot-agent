"""The minimal state that flows through every LangGraph node in V1."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Conversation messages; add_messages appends node output to prior state."""

    messages: Annotated[list[AnyMessage], add_messages]
