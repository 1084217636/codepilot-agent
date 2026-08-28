from pathlib import Path

import pytest

from app.tools.read_file import build_read_file_tool


def test_read_file_returns_workspace_content(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("LangGraph reads this file.", encoding="utf-8")
    tool = build_read_file_tool(tmp_path)

    assert tool.invoke({"path": "note.txt"}) == "LangGraph reads this file."


def test_read_file_rejects_path_escape(tmp_path: Path) -> None:
    tool = build_read_file_tool(tmp_path)

    with pytest.raises(ValueError, match="workspace"):
        tool.invoke({"path": "../../outside.txt"})
