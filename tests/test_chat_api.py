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
