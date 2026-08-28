# CodePilot Agent

一个独立、从零学习的标准 AI Coding Agent 项目。

这个项目计划用最少的抽象追通一条可解释链路：

```text
HTTP / SSE
→ conversation
→ context retrieval
→ LangGraph agent loop
→ tool calling
→ isolated workspace
→ patch / test
→ streamed result
```

它不会修改或依赖同级的 `enterprise-im-ai` 与 `agent-code-change-platform`。后续可把 IM 仓库作为本地代码检索和测试目标，但两者始终保持独立。

V1 已实现普通 JSON Chat、显式 LangGraph StateGraph、唯一的 `read_file` Tool 和 workspace 路径隔离。V1 不包含 RAG、SSE、Patch、测试执行、Branch 或 DeerFlow Runtime。

## Run V1

```bash
uv sync --all-groups
cp .env.example .env
# 填写 OpenAI-compatible provider configuration
uv run uvicorn app.main:app --app-dir backend --reload
```

Then call `POST http://127.0.0.1:8000/api/chat` with `{ "message": "hello" }`.

Read the V1 source-traced learning path from [docs/learning/01-request-flow.md](docs/learning/01-request-flow.md).
