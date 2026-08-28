"""Resolve files below the one workspace root allowed to the V1 tool."""

from __future__ import annotations

import os
from pathlib import Path


def get_workspace_root() -> Path:
    """Return the configured local workspace, creating it for first use."""

    configured = os.getenv("CODEPILOT_WORKSPACE_ROOT", "workspace")
    root = Path(configured).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_workspace_file(workspace_root: Path, requested_path: str) -> Path:
    """Return a regular file under workspace_root or raise a clear boundary error."""

    relative = Path(requested_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("path must stay inside the workspace root")
    root = workspace_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("path must stay inside the workspace root")
    if not resolved.is_file():
        raise ValueError(f"workspace file does not exist: {requested_path}")
    return resolved
