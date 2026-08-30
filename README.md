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

V1.2 已实现 `GET /health`、普通 JSON Chat、显式 LangGraph StateGraph、唯一的 `read_file` Tool、workspace 路径隔离和 `CODEPILOT_DEBUG` 教学日志。每个聊天请求都会显示独立 `request_id`、图的节点跳转、LLM 调用次数、消息类型、工具参数摘要与总耗时；不会输出 API Key、完整 Prompt 或完整文件内容。V1 不包含 RAG、SSE、Patch、测试执行、Branch 或 DeerFlow Runtime。

## Run V1

```bash
uv sync --all-groups
cp .env.example .env
# 必须把 MODEL_API_KEY=replace-me 换成自己的 OpenAI-compatible provider 配置
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

`.env.example` 中的 `replace-me` 只是防止把密钥提交到 Git 的占位值，不能调用模型。若 `/health` 正常而 `/api/chat` 返回 400，请先检查 `.env` 的 `MODEL_API_KEY`、`MODEL_BASE_URL` 和 `MODEL_NAME`。

First call `GET http://127.0.0.1:8000/health`, then call `POST /api/chat` with `{ "message": "hello" }`.

For the full two-terminal manual run, read [00-how-to-run.md](docs/learning/00-how-to-run.md). The version boundary is documented in [00-version-roadmap.md](docs/learning/00-version-roadmap.md).
