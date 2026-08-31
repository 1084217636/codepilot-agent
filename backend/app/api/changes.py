"""Human approval endpoint for V3 patch proposals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workspace.changes import PendingChange, pending_change_store

router = APIRouter(prefix="/api/changes", tags=["changes"])


class ChangeResponse(BaseModel):
    change_id: str
    path: str
    status: str
    diff: str


def change_response(change: PendingChange) -> ChangeResponse:
    return ChangeResponse(
        change_id=change.change_id,
        path=change.source.name,
        status=change.status,
        diff=change.diff,
    )


@router.get("/{change_id}", response_model=ChangeResponse)
def get_change(change_id: str) -> ChangeResponse:
    try:
        return change_response(pending_change_store.get(change_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{change_id}/approve", response_model=ChangeResponse)
def approve_change(change_id: str) -> ChangeResponse:
    try:
        return change_response(pending_change_store.approve(change_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
