from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app.api.chat import get_chat_model
from app.main import app


class FinalAnswerModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="Hello from the minimal agent.")


def test_post_chat_returns_final_answer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CODEPILOT_WORKSPACE_ROOT", str(tmp_path))
    app.dependency_overrides[get_chat_model] = lambda: FinalAnswerModel()
    try:
        response = TestClient(app).post("/api/chat", json={"message": "hello"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"answer": "Hello from the minimal agent."}
