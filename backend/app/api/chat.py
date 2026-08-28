"""One JSON endpoint: HTTP -> graph.invoke -> final AI answer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.agent.graph import build_agent_graph
from app.agent.model import build_chat_model
from app.workspace.manager import get_workspace_root

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8_000)


class ChatResponse(BaseModel):
    answer: str


def get_chat_model() -> Any:
    return build_chat_model()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, model: Any = Depends(get_chat_model)) -> ChatResponse:
    """Invoke the compiled graph and return only its final AIMessage as JSON."""

    try:
        graph = build_agent_graph(model, get_workspace_root())
        result = graph.invoke({"messages": [HumanMessage(content=request.message)]})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    final = result["messages"][-1]
    return ChatResponse(answer=str(final.content))
