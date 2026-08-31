from pathlib import Path

import pytest

from app.tools.propose_patch import build_propose_patch_tool
from app.tools.run_tests import build_run_tests_tool
from app.tools.search_code import build_search_code_tool
from app.workspace.changes import PendingChangeStore


def test_search_code_returns_workspace_relative_path_line_and_reason(tmp_path: Path) -> None:
    (tmp_path / "calculator.py").write_text("def add(left: int, right: int) -> int:\n    return left - right\n", encoding="utf-8")
    tool = build_search_code_tool(tmp_path)

    result = tool.invoke({"query": "add", "max_results": 3})

    assert "calculator.py:1" in result
    assert "reason=lexical line match" in result


def test_proposal_requires_human_approval_before_modifying_file(tmp_path: Path) -> None:
    target = tmp_path / "calculator.py"
    target.write_text("return left - right\n", encoding="utf-8")
    store = PendingChangeStore()
    tool = build_propose_patch_tool(tmp_path, store)

    result = tool.invoke(
        {"path": "calculator.py", "expected_text": "return left - right", "replacement_text": "return left + right"}
    )

    assert target.read_text(encoding="utf-8") == "return left - right\n"
    assert "status=pending_approval" in result
    change_id = result.split("change_id=", 1)[1].split("\n", 1)[0]
    approved = store.approve(change_id)
    assert approved.status == "applied"
    assert target.read_text(encoding="utf-8") == "return left + right\n"


def test_proposal_rejects_stale_file_before_applying(tmp_path: Path) -> None:
    target = tmp_path / "calculator.py"
    target.write_text("return left - right\n", encoding="utf-8")
    store = PendingChangeStore()
    tool = build_propose_patch_tool(tmp_path, store)
    result = tool.invoke(
        {"path": "calculator.py", "expected_text": "return left - right", "replacement_text": "return left + right"}
    )
    change_id = result.split("change_id=", 1)[1].split("\n", 1)[0]
    target.write_text("return left * right\n", encoding="utf-8")

    with pytest.raises(ValueError, match="changed since proposal"):
        store.approve(change_id)


def test_run_tests_uses_fixed_pytest_command_and_returns_result(tmp_path: Path) -> None:
    (tmp_path / "test_math.py").write_text("def test_truth() -> None:\n    assert 1 + 1 == 2\n", encoding="utf-8")
    tool = build_run_tests_tool(tmp_path)

    result = tool.invoke({})

    assert "exit_code=0" in result
    assert "1 passed" in result
