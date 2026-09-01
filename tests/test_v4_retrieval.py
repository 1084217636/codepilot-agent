from pathlib import Path

from app.retrieval.retriever import HybridCodeRetriever, build_context


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "refund" in text.lower() else [0.0, 1.0] for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return [1.0, 0.0] if "refund" in query.lower() else [0.0, 1.0]


def test_hybrid_retrieval_uses_symbol_lexical_semantic_and_reason(tmp_path: Path) -> None:
    (tmp_path / "payment.py").write_text(
        "def refund_order(order_id: str) -> bool:\n    return True\n", encoding="utf-8"
    )
    (tmp_path / "other.py").write_text("def unrelated() -> None:\n    pass\n", encoding="utf-8")

    results = HybridCodeRetriever(tmp_path, embedder=FakeEmbedder()).retrieve("how does refund work", top_k=2)

    assert results[0].chunk.path == "payment.py"
    assert results[0].chunk.symbol == "refund_order"
    assert "lexical" in results[0].reason
    assert "symbol" in results[0].reason
    assert "semantic" in results[0].reason


def test_retrieval_falls_back_without_embedding_and_respects_context_budget(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text("def validate_token():\n    return True\n" * 30, encoding="utf-8")

    results = HybridCodeRetriever(tmp_path).retrieve("validate token", top_k=5)
    context = build_context(results, token_budget=20)

    assert results
    assert "semantic unavailable" in results[0].reason
    assert len(context) <= 120
