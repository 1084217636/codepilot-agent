"""Explicit LangGraph nodes. No high-level Agent helper hides the model call."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState


def make_agent_node(bound_model: Any):
    """Return the graph's agent node; it invokes the model with state messages."""

    def agent(state: AgentState) -> dict[str, list]:
        response = bound_model.invoke([SystemMessage(content=SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [response]}

    return agent


def route_after_agent(state: AgentState) -> str:
    """Route to tools only when the newest AIMessage asks for one."""

    latest = state["messages"][-1]
    return "tools" if getattr(latest, "tool_calls", None) else "end"
