"""Explicit LangGraph nodes. No high-level Agent helper hides the model call."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage, ToolMessage

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.debug import debug_log, next_model_call


def make_agent_node(bound_model: Any, retrieved_context: str = ""):
    """Return the graph's agent node; it invokes the model with state messages."""

    def agent(state: AgentState) -> dict[str, list]:
        returning_from_tool = isinstance(state["messages"][-1], ToolMessage)
        message_types = ", ".join(type(message).__name__ for message in state["messages"])
        if returning_from_tool:
            debug_log(12, "ToolNode yielded ToolMessage; return to agent_node", message_type="ToolMessage")
        else:
            debug_log(6, "Enter agent_node", message_type=type(state["messages"][-1]).__name__)
        model_call = next_model_call()
        debug_log(
            7 if not returning_from_tool else 13,
            "Call LLM",
            model_call=model_call,
            state_message_count=len(state["messages"]),
            state_message_types=message_types,
        )
        retrieval_note = "" if not retrieved_context else f"\n\nRetrieved code context:\n{retrieved_context}"
        response = bound_model.invoke([SystemMessage(content=SYSTEM_PROMPT + retrieval_note), *state["messages"]])
        if getattr(response, "tool_calls", None):
            requested_tools = [
                {"name": tool_call["name"], "args": tool_call["args"]} for tool_call in response.tool_calls
            ]
            debug_log(
                8,
                "LLM returned tool_call request(s)",
                model_call=model_call,
                message_type="AIMessage",
                tool_call_count=len(requested_tools),
                tools=requested_tools,
            )
        elif returning_from_tool:
            debug_log(14, "LLM returned final answer", model_call=model_call, message_type="AIMessage", has_tool_calls=False)
        else:
            debug_log(8, "LLM returned AIMessage", model_call=model_call, message_type="AIMessage", has_tool_calls=False)
        return {"messages": [response]}

    return agent


def route_after_agent(state: AgentState) -> str:
    """Route to tools only when the newest AIMessage asks for one."""

    latest = state["messages"][-1]
    if getattr(latest, "tool_calls", None):
        debug_log(9, "Route agent -> ToolNode")
        return "tools"
    debug_log(15, "No tool call -> route agent -> END")
    return "end"
