from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from openai import APIConnectionError
from httpx import Request

from app.api.chat import get_chat_model
from app.agent.model import build_chat_model
from app.main import app


class FinalAnswerModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="Hello from the minimal agent.")


class UnavailableModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        raise APIConnectionError(message="provider unavailable", request=Request("POST", "https://example.test"))


class StreamingToolModel:
    """Deterministic double for checking the real Agent Loop's SSE event order."""

    def __init__(self) -> None:
        self.calls = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"path": "answer.txt"},
                        "id": "stream-read-1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="The streamed answer is 42.")


def test_post_chat_returns_final_answer(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("CODEPILOT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("CODEPILOT_DEBUG", "true")
    app.dependency_overrides[get_chat_model] = lambda: FinalAnswerModel()
    try:
        response = TestClient(app).post("/api/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"answer": "Hello from the minimal agent."}
    logs = capsys.readouterr().out
    assert "Request finished" in logs
    assert "model_calls=1" in logs


def test_health_reports_service_ready() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_chat_returns_clear_error_when_model_provider_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CODEPILOT_WORKSPACE_ROOT", str(tmp_path))
    app.dependency_overrides[get_chat_model] = lambda: UnavailableModel()
    try:
        response = TestClient(app).post("/api/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "Model provider request failed. Check MODEL_API_KEY, MODEL_BASE_URL, and MODEL_NAME."}


def test_post_chat_rejects_example_api_key(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "replace-me")
    app.dependency_overrides.pop(get_chat_model, None)

    response = TestClient(app).post("/api/chat", json={"message": "hello"})

    assert response.status_code == 400
    assert "example value" in response.json()["detail"]


def test_post_chat_stream_emits_agent_progress_and_final_answer(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("CODEPILOT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("CODEPILOT_DEBUG", "true")
    (tmp_path / "answer.txt").write_text("42", encoding="utf-8")
    app.dependency_overrides[get_chat_model] = lambda: StreamingToolModel()
    try:
        response = TestClient(app).post("/api/chat/stream", json={"message": "Read answer.txt"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: status" in body
    assert "event: tool_call" in body
    assert '"name": "read_file"' in body
    assert "event: tool_result" in body
    assert "event: answer" in body
    assert "The streamed answer is 42." in body
    assert "event: done" in body
    assert '"model_calls": 2' in body
    assert body.index("event: tool_call") < body.index("event: tool_result") < body.index("event: answer")
    logs = capsys.readouterr().out
    assert "SSE request finished" in logs
    assert "model_calls=2" in logs
