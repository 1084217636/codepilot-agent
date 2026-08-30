"""One JSON endpoint: HTTP -> graph.invoke -> final AI answer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from openai import APIError
from pydantic import BaseModel, Field

from app.agent.graph import build_agent_graph
from app.agent.model import build_chat_model
from app.debug import begin_trace, debug_log, trace_summary
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
