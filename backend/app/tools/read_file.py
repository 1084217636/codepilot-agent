"""The only V1 tool: bounded, workspace-scoped file reading."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool, tool

from app.workspace.manager import resolve_workspace_file

MAX_READ_CHARS = 20_000


def build_read_file_tool(workspace_root: Path) -> BaseTool:
    """Build a typed Tool whose closure fixes the allowed workspace root."""

    @tool("read_file", parse_docstring=True)
    def read_file(path: str) -> str:
        """Read one UTF-8 text file below the configured workspace root.

        Args:
            path: Relative path below the workspace root.
        """

        source = resolve_workspace_file(workspace_root, path)
        return source.read_text(encoding="utf-8", errors="replace")[:MAX_READ_CHARS]

    return read_file
