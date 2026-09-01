import json
from pathlib import Path

from app.evals.retrieval_eval import evaluate_dataset


def test_evaluator_reports_file_and_symbol_recall(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text("def validate_token(token: str) -> bool:\n    return bool(token)\n", encoding="utf-8")
    dataset = tmp_path / "tasks.json"
    dataset.write_text(
        json.dumps(
            {"tasks": [{"id": "one", "split": "dev", "question": "where validate token", "expected_files": ["service.py"], "expected_symbols": ["validate_token"]}]}
        ),
        encoding="utf-8",
    )

    report = evaluate_dataset(tmp_path, dataset, top_k=2, token_budget=100)

    assert report["task_count"] == 1
    assert report["file_recall_at_k"] == 1.0
    assert report["symbol_recall_at_k"] == 1.0
    assert report["average_context_chars"] > 0
