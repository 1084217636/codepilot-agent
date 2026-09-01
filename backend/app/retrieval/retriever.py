"""Lightweight hybrid code retrieval without a vector database."""

from __future__ import annotations

import ast
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    text: str
    symbol: str | None = None


@dataclass(frozen=True)
class RetrievalResult:
    chunk: CodeChunk
    score: float
    reason: str


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


def _tokens(text: str) -> set[str]:
    return {part for part in "".join(char if char.isalnum() else " " for char in text.casefold()).split() if part}


def _chunks(root: Path) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    for source in sorted(root.rglob("*.py")):
        if not source.is_file() or any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in source.parts):
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        relative = source.relative_to(root).as_posix()
        try:
            tree = ast.parse(text)
            nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        except SyntaxError:
            nodes = []
        if nodes:
            for node in nodes:
                start, end = node.lineno, node.end_lineno or node.lineno
                chunks.append(CodeChunk(relative, start, end, "\n".join(lines[start - 1 : end]), node.name))
        elif text:
            chunks.append(CodeChunk(relative, 1, len(lines), text, None))
    return chunks


def _cosine(left: list[float], right: list[float]) -> float:
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return 0.0 if not denominator else sum(x * y for x, y in zip(left, right)) / denominator


class HybridCodeRetriever:
    """Fuse lexical, symbol and optional embedding signals for a small workspace."""

    def __init__(self, workspace_root: Path, embedder: Embedder | None = None) -> None:
        self.root = workspace_root.resolve()
        self.embedder = embedder
        self.chunks = _chunks(self.root)
        self._vectors: list[list[float]] | None = None
        if embedder:
            try:
                self._vectors = embedder.embed_documents([chunk.text for chunk in self.chunks])
            except Exception:
                self._vectors = None

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievalResult]:
        query_tokens = _tokens(query)
        query_vector: list[float] | None = None
        if self.embedder and self._vectors is not None:
            try:
                query_vector = self.embedder.embed_query(query)
            except Exception:
                pass
        results: list[RetrievalResult] = []
        for index, chunk in enumerate(self.chunks):
            lexical = len(query_tokens & _tokens(f"{chunk.path} {chunk.text}")) / max(len(query_tokens), 1)
            symbol = len(query_tokens & _tokens(chunk.symbol or "")) / max(len(query_tokens), 1)
            semantic = _cosine(query_vector, self._vectors[index]) if query_vector and self._vectors else 0.0
            score = 0.5 * lexical + 0.3 * symbol + 0.2 * semantic
            if score <= 0:
                continue
            parts = [f"lexical={lexical:.2f}", f"symbol={symbol:.2f}"]
            parts.append(f"semantic={semantic:.2f}" if query_vector else "semantic unavailable")
            results.append(RetrievalResult(chunk, score, "; ".join(parts)))
        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def build_context(results: list[RetrievalResult], token_budget: int = 800) -> str:
    """Fit top chunks into a simple approximate token budget for the agent prompt."""

    remaining = token_budget
    sections: list[str] = []
    for result in results:
        header = f"[{result.chunk.path}:{result.chunk.start_line}-{result.chunk.end_line}; {result.reason}]\n"
        allowed_chars = max(remaining * 4 - len(header), 0)
        if allowed_chars <= 0:
            break
        text = result.chunk.text[:allowed_chars]
        sections.append(header + text)
        remaining -= math.ceil((len(header) + len(text)) / 4)
    return "\n\n".join(sections)


def configured_embedder() -> Embedder | None:
    """Create an optional OpenAI-compatible embedding client from explicit V4 env vars."""

    model = os.getenv("EMBEDDING_MODEL", "").strip()
    api_key = os.getenv("EMBEDDING_API_KEY", "").strip()
    if not model or not api_key:
        return None
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=model,
        api_key=api_key,
        base_url=os.getenv("EMBEDDING_BASE_URL") or None,
    )
