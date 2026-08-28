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

V1.2 已实现 `GET /health`、普通 JSON Chat、显式 LangGraph StateGraph、唯一的 `read_file` Tool、workspace 路径隔离和 `CODEPILOT_DEBUG` 教学日志。V1 不包含 RAG、SSE、Patch、测试执行、Branch 或 DeerFlow Runtime。

## Run V1

```bash
uv sync --all-groups
cp .env.example .env
# 填写 OpenAI-compatible provider configuration and CODEPILOT_DEBUG=true
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

First call `GET http://127.0.0.1:8000/health`, then call `POST /api/chat` with `{ "message": "hello" }`.

For the full two-terminal manual run, read [00-how-to-run.md](docs/learning/00-how-to-run.md). The version boundary is documented in [00-version-roadmap.md](docs/learning/00-version-roadmap.md).
