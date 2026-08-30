from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.graph import build_agent_graph
from app.debug import begin_trace


class ScriptedToolCallingModel:
    """A deterministic model double that follows one real tool-call protocol."""

    def __init__(self) -> None:
        self.bound_tools = []
        self.calls = 0

    def bind_tools(self, tools):
        self.bound_tools = tools
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
                        "id": "call-read-1",
                        "type": "tool_call",
                    }
                ],
            )
        assert any(isinstance(message, ToolMessage) for message in messages)
        return AIMessage(content="The file says: 42.")


def test_agent_graph_runs_human_tool_ai_message_sequence(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("CODEPILOT_DEBUG", "true")
    begin_trace("test-tool-loop")
    (tmp_path / "answer.txt").write_text("42", encoding="utf-8")
    model = ScriptedToolCallingModel()
    graph = build_agent_graph(model, tmp_path)

    result = graph.invoke({"messages": [HumanMessage(content="Read answer.txt and tell me the value.")]})

    assert model.bound_tools
    assert [type(message) for message in result["messages"]] == [HumanMessage, AIMessage, ToolMessage, AIMessage]
    assert result["messages"][1].tool_calls[0]["name"] == "read_file"
    assert result["messages"][2].content == "42"
    assert result["messages"][-1].content == "The file says: 42."
    logs = capsys.readouterr().out
    assert "request_id='test-tool-loop'" in logs
    assert "model_call=1" in logs
    assert "model_call=2" in logs
    assert "LLM returned tool_call" in logs
    assert "Execute project Python tool: read_file" in logs
    assert "ToolNode yielded ToolMessage" in logs
    assert "LLM returned final answer" in logs
