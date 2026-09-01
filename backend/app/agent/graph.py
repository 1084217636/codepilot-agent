"""The visible V3 StateGraph: START -> agent -> tools? -> agent/END."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.nodes import make_agent_node, route_after_agent
from app.agent.state import AgentState
from app.debug import debug_log
from app.tools.propose_patch import build_propose_patch_tool
from app.tools.read_file import build_read_file_tool
from app.tools.run_tests import build_run_tests_tool
from app.tools.search_code import build_search_code_tool
from app.workspace.changes import pending_change_store


def build_agent_graph(model: Any, workspace_root: Path, retrieved_context: str = ""):
    """Bind bounded V3 Tools, declare nodes/edges, compile, and return the graph."""

    read_file = build_read_file_tool(workspace_root)
    search_code = build_search_code_tool(workspace_root)
    propose_patch = build_propose_patch_tool(workspace_root, pending_change_store)
    run_tests = build_run_tests_tool(workspace_root)
    tools = [read_file, search_code, propose_patch, run_tests]
    bound_model = model.bind_tools(tools)
    debug_log(
        3,
        "Bind tool schema to LLM and build StateGraph",
        nodes="agent, tools",
        tool_names=", ".join(tool.name for tool in tools),
        workspace_root=str(workspace_root),
    )

    builder = StateGraph(AgentState)
    builder.add_node("agent", make_agent_node(bound_model, retrieved_context))
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
    builder.add_edge("tools", "agent")
    graph = builder.compile()
    debug_log(4, "Compile graph", edges="START->agent; agent->tools|END; tools->agent")
    return graph
