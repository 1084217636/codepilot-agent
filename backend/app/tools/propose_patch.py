"""A Tool that creates a reviewable patch proposal but never writes immediately."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from app.debug import debug_log
from app.workspace.changes import PendingChangeStore
from app.workspace.manager import resolve_workspace_file


def build_propose_patch_tool(workspace_root: Path, change_store: PendingChangeStore) -> BaseTool:
    """Build a deterministic single-replacement proposal Tool."""

    @tool("propose_patch", parse_docstring=True)
    def propose_patch(path: str, expected_text: str, replacement_text: str) -> str:
        """Create one exact, reviewable text replacement without writing the file.

        Args:
            path: Relative workspace file path to change.
            expected_text: Exact old text that must occur exactly once.
            replacement_text: New text to substitute for expected_text.
        """

        debug_log(10, "Execute project Python tool: propose_patch", path=path)
        source = resolve_workspace_file(workspace_root, path)
        original = source.read_text(encoding="utf-8")
        occurrences = original.count(expected_text)
        if occurrences != 1:
            raise ValueError(f"expected_text must occur exactly once; found {occurrences}")
        proposed = original.replace(expected_text, replacement_text, 1)
        diff = "".join(
            unified_diff(
                original.splitlines(keepends=True),
                proposed.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
        change = change_store.add(source, original, proposed, diff)
        debug_log(11, "propose_patch created pending change", change_id=change.change_id, status=change.status)
        return f"change_id={change.change_id}\nstatus=pending_approval\n{change.diff}"

    return propose_patch
