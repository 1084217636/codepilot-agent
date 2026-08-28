"""Explicit LangGraph nodes. No high-level Agent helper hides the model call."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage, ToolMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.debug import debug_log


def make_agent_node(bound_model: Any):
    """Return the graph's agent node; it invokes the model with state messages."""

    def agent(state: AgentState) -> dict[str, list]:
        returning_from_tool = isinstance(state["messages"][-1], ToolMessage)
        if returning_from_tool:
            debug_log(10, "ToolNode created ToolMessage", message_type="ToolMessage")
            debug_log(11, "Return to agent_node")
            debug_log(12, "Calling LLM again", message_count=len(state["messages"]))
        else:
            debug_log(4, "Enter agent_node", message_type=type(state["messages"][-1]).__name__)
            debug_log(5, "Calling LLM", message_count=len(state["messages"]))
        response = bound_model.invoke([SystemMessage(content=SYSTEM_PROMPT), *state["messages"]])
        if getattr(response, "tool_calls", None):
            tool_call = response.tool_calls[0]
            debug_log(6, "LLM returned tool_call", message_type="AIMessage", tool=tool_call["name"], args=tool_call["args"])
        elif returning_from_tool:
            debug_log(13, "LLM returned final answer", message_type="AIMessage", has_tool_calls=False)
        else:
            debug_log(6, "LLM returned AIMessage", message_type="AIMessage", has_tool_calls=False)
        return {"messages": [response]}

    return agent


def route_after_agent(state: AgentState) -> str:
    """Route to tools only when the newest AIMessage asks for one."""

    latest = state["messages"][-1]
    if getattr(latest, "tool_calls", None):
        debug_log(7, "Enter ToolNode")
        return "tools"
    debug_log(7, "No tool call -> finish")
    return "end"
