# Changelog

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
