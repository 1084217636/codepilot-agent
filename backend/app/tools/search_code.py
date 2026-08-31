"""A small lexical code-search Tool; semantic retrieval belongs to V4."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool, tool

from app.debug import debug_log

TEXT_SUFFIXES = {".go", ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}
MAX_FILES_SCANNED = 200


def build_search_code_tool(workspace_root: Path) -> BaseTool:
    """Build a bounded lexical search tool for small local workspaces."""

    @tool("search_code", parse_docstring=True)
    def search_code(query: str, max_results: int = 5) -> str:
        """Find text occurrences in workspace source files.

        Args:
            query: Case-insensitive text to find in a file path or line content.
            max_results: Maximum matching lines to return, from 1 through 10.
        """

        needle = query.strip().casefold()
        if not needle:
            raise ValueError("query must not be empty")
        debug_log(10, "Execute project Python tool: search_code", query_chars=len(needle), max_results=max_results)
        limit = min(max(max_results, 1), 10)
        matches: list[str] = []
        root = workspace_root.resolve()
        for source in sorted(root.rglob("*"))[:MAX_FILES_SCANNED]:
            if not source.is_file() or source.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative_path = source.relative_to(root).as_posix()
            path_matches = needle in relative_path.casefold()
            for line_number, line in enumerate(source.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                if path_matches or needle in line.casefold():
                    matches.append(f"{relative_path}:{line_number}: {line.strip()} [reason=lexical line match]")
                    if len(matches) >= limit:
                        debug_log(11, "search_code result", result_count=len(matches))
                        return "\n".join(matches)
        debug_log(11, "search_code result", result_count=len(matches))
        return "\n".join(matches) if matches else "No lexical code matches found."

    return search_code
