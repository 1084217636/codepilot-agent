"""One JSON endpoint: HTTP -> graph.invoke -> final AI answer."""

from __future__ import annotations

import json
import re
from typing import Any, Iterator

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from openai import APIError
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from app.agent.graph import build_agent_graph
from app.agent.model import build_chat_model
from app.debug import RequestTrace, activate_trace, begin_trace, debug_log, trace_summary
from app.workspace.manager import get_workspace_root

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)


class ChatResponse(BaseModel):
    answer: str


def get_chat_model() -> Any:
    """Build the request model and turn local configuration mistakes into HTTP 400."""

    try:
        return build_chat_model()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def sse_event(event: str, data: dict[str, Any]) -> str:
    """Encode one Server-Sent Event without exposing complete prompts or secrets."""

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def tool_result_summary(name: str | None, content: str) -> dict[str, Any]:
    """Expose safe V3 client facts, never full file or test output in SSE."""

    summary: dict[str, Any] = {"name": name or "unknown", "chars": len(content)}
    if name == "propose_patch":
        change_id = re.search(r"^change_id=([a-z0-9]+)$", content, flags=re.MULTILINE)
        summary["status"] = "pending_approval"
        if change_id:
            summary["change_id"] = change_id.group(1)
    elif name == "run_tests":
        exit_code = re.search(r"^exit_code=([^\n]+)$", content, flags=re.MULTILINE)
        if exit_code:
            summary["exit_code"] = exit_code.group(1)
    return summary


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, model: Any = Depends(get_chat_model)) -> ChatResponse:
    """Invoke the compiled graph and return only its final AIMessage as JSON."""

    begin_trace()
    try:
        debug_log(1, "HTTP request received", endpoint="POST /api/chat", user_message_chars=len(request.message))
        human = HumanMessage(content=request.message)
        debug_log(2, "Create initial AgentState", message_type="HumanMessage", message_count=1)
        graph = build_agent_graph(model, get_workspace_root())
        debug_log(5, "Invoke compiled graph")
        result = graph.invoke({"messages": [human]})
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail="Model provider request failed. Check MODEL_API_KEY, MODEL_BASE_URL, and MODEL_NAME.",
        ) from exc
    final = result["messages"][-1]
    message_types = ", ".join(type(message).__name__ for message in result["messages"])
    debug_log(16, "LangGraph finished", final_message_types=message_types)
    debug_log(17, "Request finished", **trace_summary())
    return ChatResponse(answer=str(final.content))


def stream_chat_events(request: ChatRequest, model: Any, trace: RequestTrace) -> Iterator[str]:
    """Run the same graph and emit completed node facts as SSE events.

    V2 deliberately streams workflow progress and the final answer, rather than
    model token chunks. This keeps the existing synchronous agent node visible
    and avoids introducing async token aggregation in the same learning stage.
    """

    try:
        activate_trace(trace)
        debug_log(1, "SSE request received", endpoint="POST /api/chat/stream", user_message_chars=len(request.message))
        yield sse_event("status", {"stage": "started", "request_id": trace_summary()["request_id"]})

        activate_trace(trace)
        human = HumanMessage(content=request.message)
        debug_log(2, "Create initial AgentState", message_type="HumanMessage", message_count=1)
        graph = build_agent_graph(model, get_workspace_root())
        yield sse_event("status", {"stage": "graph_compiled", "request_id": trace_summary()["request_id"]})

        activate_trace(trace)
        debug_log(5, "Stream compiled graph updates")
        final_answer = ""
        updates = iter(graph.stream({"messages": [human]}, stream_mode="updates"))
        while True:
            activate_trace(trace)
            try:
                update = next(updates)
            except StopIteration:
                break
            for node_update in update.values():
                for message in node_update.get("messages", []):
                    if getattr(message, "tool_calls", None):
                        for tool_call in message.tool_calls:
                            yield sse_event("tool_call", {"name": tool_call["name"], "args": tool_call["args"]})
                    elif message.type == "tool":
                        yield sse_event(
                            "tool_result",
                            tool_result_summary(message.name, str(message.content)),
                        )
                    elif message.type == "ai":
                        final_answer = str(message.content)
                        yield sse_event("answer", {"content": final_answer})

        if not final_answer:
            raise ValueError("agent finished without a final answer")
        activate_trace(trace)
        debug_log(16, "LangGraph stream finished")
        yield sse_event("done", trace_summary())
        activate_trace(trace)
        debug_log(17, "SSE request finished", **trace_summary())
    except (APIError, ValueError):
        activate_trace(trace)
        debug_log(16, "SSE agent flow failed")
        yield sse_event("error", {"message": "Agent flow failed. Check model configuration or tool input."})
        activate_trace(trace)
        yield sse_event("done", trace_summary())


@router.post("/chat/stream")
def chat_stream(request: ChatRequest, model: Any = Depends(get_chat_model)) -> StreamingResponse:
    """Expose the V2 workflow trace as a standard SSE response."""

    # Create the mutable request trace before StreamingResponse moves generator
    # iteration to its worker thread; all yielded chunks then share this trace.
    trace = begin_trace()
    return StreamingResponse(
        stream_chat_events(request, model, trace),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
