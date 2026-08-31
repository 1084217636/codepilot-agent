# 04 V2：SSE 让 Agent 过程对客户端可见

## 概念是什么

SSE（Server-Sent Events）是一种 HTTP 响应格式。服务器不必等所有工作结束才返回一个 JSON，而是保持本次响应打开，连续发送若干事件：

```text
event: status
data: {"stage":"started"}

event: tool_call
data: {"name":"read_file","args":{"path":"demo/hello.py"}}
```

每个事件由 `event:`、`data:` 和一个空行组成。客户端读到空行，就知道收到了一条完整事件。

## 为什么需要它

普通 `POST /api/chat` 的体验是：用户等待 Agent 完全结束，才收到 `{ "answer": "..." }`。当模型需要调用工具时，用户不知道它是在思考、读取文件还是报错。

V2 的 `POST /api/chat/stream` 使用同一张 LangGraph 图，但把已经完成的执行阶段逐步通知客户端：

```text
status(started)
→ status(graph_compiled)
→ tool_call
→ tool_result
→ answer
→ done
```

这让客户端能显示“正在读取文件”之类的状态。它不是额外调用一次模型；同一问题是否调用 1 次或 2 次 DeepSeek，仍取决于 Agent 是否需要 Tool。

## 当前项目怎么实现

入口在 [api/chat.py](../../backend/app/api/chat.py) 的 `chat_stream()`：

```text
POST /api/chat/stream
→ StreamingResponse(..., media_type="text/event-stream")
→ stream_chat_events()
→ graph.stream(..., stream_mode="updates")
→ 将每个 Node 的新 Message 转为 SSE event
```

`graph.stream(..., stream_mode="updates")` 给出的是每个 **Node 完成后** 对 State 的更新：

| LangGraph 新消息 | SSE 事件 | 客户端含义 |
| --- | --- | --- |
| `AIMessage.tool_calls` | `tool_call` | 模型决定请求哪个工具 |
| `ToolMessage` | `tool_result` | 本地工具已完成，返回字符数摘要 |
| 不含 Tool Call 的 `AIMessage` | `answer` | 模型产生最终回答 |

最后的 `done` 事件包含本次 `request_id`、`model_calls` 和 `elapsed_ms`。

## 它不是什么

V2 还没有做 Token Streaming。`agent` Node 目前调用的是：

```python
bound_model.invoke(...)
```

它会等待一次 DeepSeek 调用完整结束。因此 `answer` 事件一次发送完整答案，并不会逐字显示。逐 Token 流式输出需要模型的 `.stream()`、Chunk 聚合、Tool Call 参数流式拼接以及 async 处理；这是一个独立学习主题，不能和第一个 SSE 版本混在一起。

## 怎样亲手测试

终端 1 启动服务：

```bash
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

终端 2 使用 `curl -N`，其中 `-N` 表示不要缓冲响应：

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"请读取 demo/hello.py，并用一句话说明它的功能。"}'
```

正常情况会先看到两条 `status`，接着是 `tool_call`、`tool_result`、`answer` 与 `done`。若这次问题不需要工具，则没有中间两条工具事件，且 `done.data.model_calls` 通常为 `1`。

## 面试怎么说

> V2 在原有同步 LangGraph Agent Loop 外增加 SSE 过程事件流。服务端通过 `graph.stream(stream_mode="updates")` 观察节点完成后的 State 更新，将模型 Tool Call、ToolMessage 和最终 AIMessage 映射为结构化 SSE 事件。这样客户端可以展示 Agent 的执行进展，同时保留 request_id、模型调用次数和耗时等可观测信息。当前版本明确只流式发送阶段事件和最终答案，不把它表述为逐 Token 流式生成。
