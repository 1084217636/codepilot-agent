"""Evaluate fixed, source-grounded retrieval tasks without calling an LLM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.retrieval.retriever import HybridCodeRetriever, build_context


def evaluate_dataset(workspace_root: Path, dataset_path: Path, top_k: int, token_budget: int, split: str | None = None) -> dict[str, Any]:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    tasks = [task for task in dataset["tasks"] if split is None or task["split"] == split]
    retriever = HybridCodeRetriever(workspace_root)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        results = retriever.retrieve(task["question"], top_k=top_k)
        paths = {item.chunk.path for item in results}
        symbols = {item.chunk.symbol for item in results if item.chunk.symbol}
        expected_files = set(task["expected_files"])
        expected_symbols = set(task["expected_symbols"])
        context = build_context(results, token_budget=token_budget)
        rows.append({
            "id": task["id"],
            "file_recall": len(paths & expected_files) / len(expected_files),
            "symbol_recall": len(symbols & expected_symbols) / len(expected_symbols),
            "context_chars": len(context),
            "retrieved": [{"path": item.chunk.path, "symbol": item.chunk.symbol, "reason": item.reason} for item in results],
        })
    count = len(rows)
    return {
        "task_count": count,
        "top_k": top_k,
        "token_budget": token_budget,
        "file_recall_at_k": sum(row["file_recall"] for row in rows) / count if count else 0,
        "symbol_recall_at_k": sum(row["symbol_recall"] for row in rows) / count if count else 0,
        "average_context_chars": sum(row["context_chars"] for row in rows) / count if count else 0,
        "tasks": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--token-budget", type=int, default=800)
    parser.add_argument("--split", choices=["dev", "holdout"])
    args = parser.parse_args()
    report = evaluate_dataset(args.workspace, args.dataset, args.top_k, args.token_budget, args.split)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "tasks"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
