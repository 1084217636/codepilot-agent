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

V4 已实现 V3 Coding Agent 闭环，并在 Agent 前加入轻量 Hybrid Code RAG：Python symbol Chunk、lexical/symbol/optional semantic 召回、Top-K 和 Token Budget。Embedding 未配置时自动降级，不包含数据库、Branch、前端或 DeerFlow Runtime。

## Run V1

```bash
uv sync --all-groups
cp .env.example .env
# 必须把 MODEL_API_KEY=replace-me 换成自己的 OpenAI-compatible provider 配置
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

`.env.example` 中的 `replace-me` 只是防止把密钥提交到 Git 的占位值，不能调用模型。若 `/health` 正常而 `/api/chat` 返回 400，请先检查 `.env` 的 `MODEL_API_KEY`、`MODEL_BASE_URL` 和 `MODEL_NAME`。

First call `GET http://127.0.0.1:8000/health`, then call `POST /api/chat` with `{ "message": "hello" }`.

To observe the V2 Agent workflow as SSE, call `POST /api/chat/stream`; see [04-sse-streaming.md](docs/learning/04-sse-streaming.md).

For the V3 search / Patch proposal / human approval / test loop, see [05-v3-code-change-loop.md](docs/learning/05-v3-code-change-loop.md).

For the full two-terminal manual run, read [00-how-to-run.md](docs/learning/00-how-to-run.md). The version boundary is documented in [00-version-roadmap.md](docs/learning/00-version-roadmap.md).
