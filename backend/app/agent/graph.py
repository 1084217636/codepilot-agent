"""The visible V1 StateGraph: START -> agent -> tools? -> agent/END."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.nodes import make_agent_node, route_after_agent
from app.agent.state import AgentState
from app.tools.read_file import build_read_file_tool


def build_agent_graph(model: Any, workspace_root: Path):
    """Bind the one Tool, declare nodes/edges, compile, and return the runnable graph."""

    read_file = build_read_file_tool(workspace_root)
    bound_model = model.bind_tools([read_file])

    builder = StateGraph(AgentState)
    builder.add_node("agent", make_agent_node(bound_model))
    builder.add_node("tools", ToolNode([read_file]))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
    builder.add_edge("tools", "agent")
    return builder.compile()
