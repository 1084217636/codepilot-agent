# Changelog

## V4：Hybrid Code RAG，当前版本

- 函数/类级 Python Chunk、lexical + symbol + optional semantic 融合。
- Top-K、近似 Token Budget Context Builder 与 Embedding fallback。
- SSE `retrieval` 事件；不增加向量数据库或持久化。

## V3：Coding Agent 最小修改闭环，当前版本

新增：

- workspace 限制下的 lexical `search_code` 和固定 pytest `run_tests` Tool。
- 不直接写盘的 `propose_patch` Tool，生成 `change_id` 和 unified Diff。
- 人工 `POST /api/changes/{change_id}/approve` 批准接口，以及批准前的 stale 文件检查。
- V3 演示 Bug、真实 DeepSeek 提案验证与 13 项自动测试。

边界：检索不是 RAG；提案是进程内内存数据；不含数据库、前端、Branch 或任意 Shell。

## V2：SSE Agent 过程事件流，当前版本

新增：

- `POST /api/chat/stream`，返回标准 `text/event-stream`。
- `status`、`tool_call`、`tool_result`、`answer`、`done` 事件。
- 流式请求内的 request Trace 传播和对 `model_calls` 的真实统计。

边界：本版发送节点完成事件和最终答案，不实现逐 Token Streaming，不增加数据库、RAG、Patch、测试执行或 Branch。

## V1.2：Tool Calling Agent，当前版本

新增：

- `read_file` Tool、`model.bind_tools`、`ToolNode`、条件 Edge。
- `workspace/demo/README.md` 与 `hello.py` 示例。
- `CODEPILOT_DEBUG` 教学日志：每次请求记录 request ID、StateGraph 节点跳转、消息类型、实际 LLM 调用次数、工具参数摘要和总耗时；不记录密钥、完整 Prompt 或完整文件内容。

系统结构：

```text
User → FastAPI → LangGraph → Agent → LLM
→ tool_call → Tool → ToolMessage → Agent → LLM → Answer
```

新增知识：Function Calling、Tool Calling、ToolMessage、Agent Loop。

## V1.1：LangGraph 单节点

新增：`AgentState`、agent Node、StateGraph、Edge、compile、invoke。

```text
User → FastAPI → LangGraph → Agent → LLM → Answer
```

## V1.0：普通 LLM Chat

目标结构：

```text
User → FastAPI → LLM → Answer
```

## V0.1：FastAPI 最小服务

当前以 `GET /health` 保留该层的可观察证据：

```text
User → FastAPI → Response
```

## V0：项目骨架

README、AGENTS、gitignore 与独立 Git 仓库初始化。
