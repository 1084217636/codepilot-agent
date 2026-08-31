"""In-memory, human-approved workspace change proposals for V3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from uuid import uuid4


@dataclass
class PendingChange:
    change_id: str
    source: Path
    original_content: str
    proposed_content: str
    diff: str
    status: str = "pending_approval"


class PendingChangeStore:
    """Keep short-lived proposals separate from real workspace writes.

    V3 intentionally keeps this in memory. A process restart loses proposals;
    persistent Thread/Branch data belongs to V5, not this first change loop.
    """

    def __init__(self) -> None:
        self._changes: dict[str, PendingChange] = {}
        self._lock = RLock()

    def add(self, source: Path, original_content: str, proposed_content: str, diff: str) -> PendingChange:
        change = PendingChange(
            change_id=uuid4().hex[:12],
            source=source,
            original_content=original_content,
            proposed_content=proposed_content,
            diff=diff,
        )
        with self._lock:
            self._changes[change.change_id] = change
        return change

    def get(self, change_id: str) -> PendingChange:
        with self._lock:
            change = self._changes.get(change_id)
        if change is None:
            raise ValueError("change proposal does not exist")
        return change

    def approve(self, change_id: str) -> PendingChange:
        """Apply exactly the reviewed proposal only if the target did not change."""

        with self._lock:
            change = self.get(change_id)
            if change.status != "pending_approval":
                raise ValueError(f"change is not pending approval: {change.status}")
            current_content = change.source.read_text(encoding="utf-8")
            if current_content != change.original_content:
                change.status = "stale"
                raise ValueError("workspace file changed since proposal; create a new proposal")
            change.source.write_text(change.proposed_content, encoding="utf-8")
            change.status = "applied"
            return change


pending_change_store = PendingChangeStore()
