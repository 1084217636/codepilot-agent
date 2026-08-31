"""A fixed, workspace-scoped pytest Tool; it never accepts shell commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from app.debug import debug_log

MAX_OUTPUT_CHARS = 4_000


def build_run_tests_tool(workspace_root: Path) -> BaseTool:
    """Build a Tool that can only run the fixed pytest command in workspace_root."""

    @tool("run_tests", parse_docstring=True)
    def run_tests() -> str:
        """Run pytest -q in the configured workspace and return bounded output."""

        try:
            debug_log(10, "Execute project Python tool: run_tests", command="python -m pytest -q", timeout_seconds=20)
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return f"exit_code=timeout\n{str(exc)[:MAX_OUTPUT_CHARS]}"
        output = (completed.stdout + completed.stderr).strip()[:MAX_OUTPUT_CHARS]
        debug_log(11, "run_tests finished", exit_code=completed.returncode, output_chars=len(output))
        return f"exit_code={completed.returncode}\n{output}"

    return run_tests
