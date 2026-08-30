# 01 一次请求怎样走到最终回答

![CodePilot V1 Agent Tool Flow](assets/01-agent-tool-flow.png)

## 概念是什么

本项目的入口是 `POST /api/chat`。浏览器或 curl 传入 JSON：

```json
{"message": "请读取 note.txt"}
```

V1 只返回普通 JSON，不使用 SSE。它要证明的是最小主链：HTTP 请求变成 LangGraph State，模型可以选择调用 Tool，Tool 结果再进入模型，最后返回答案。

运行时先按 [00-how-to-run.md](00-how-to-run.md) 操作。`CODEPILOT_DEBUG=true` 时，终端会显示 `[CodePilot][01]` 到 `[17]`。同一个 `request_id` 的日志属于同一次请求；其中 `model_call=1`、`model_call=2` 是该请求实际向配置的 DeepSeek / OpenAI-compatible 模型发出的第几次调用，不是 LangGraph 的虚拟计数。

## 为什么需要这条链

直接调用一次 LLM 只能回答模型已有知识。Coding Agent 必须能够在需要时读取外部文件，因此要有一个循环：模型先决定要不要调用工具，程序执行工具，模型看见结果后继续回答。

## 我的项目怎么实现

```text
app/api/chat.py::chat
→ app/agent/graph.py::build_agent_graph
→ compiled_graph.invoke({messages: [HumanMessage]})
→ app/agent/nodes.py::agent
→ bound_model.invoke(SystemMessage + state.messages)
→ AIMessage
→ route_after_agent
→ ToolNode 或 END
→ ChatResponse(answer)
```

`chat()` 的输入是 `ChatRequest.message`，输出是 `ChatResponse.answer`。它每次请求创建一张很小的图，调用同步 `graph.invoke()`，读取最后一个 AIMessage 的内容返回 JSON。

观察时，`[01]` 和 `[02]` 属于 HTTP 层；`[03]` 到 `[05]` 是 Tool Schema 与图的装配；`[06]` 到 `[15]` 是 Agent Loop；`[16]` 和 `[17]` 是本次图执行的汇总。

没有 Tool Call 时，图走：`START → agent → END`。这就是本轮先证明的普通 Chat 路径：HTTP → FastAPI → LLM → Final Answer。

有 Tool Call 时，图走：`START → agent → tools → agent → END`。具体循环见 [03 Tool Calling](03-tool-calling.md)。

## 怎样读一次真实日志

对“读取 `demo/hello.py`”的问题，完整路径应是：

```text
[01] HTTP request received
[02] Create initial AgentState
[03] Bind tool schema to LLM and build StateGraph
[04] Compile graph
[05] Invoke compiled graph
[06] Enter agent_node
[07] Call LLM | model_call=1 | state_message_types='HumanMessage'
[08] LLM returned tool_call | tool='read_file'
[09] Route agent -> ToolNode
[10] Execute project Python tool: read_file
[11] read_file success
[12] ToolNode yielded ToolMessage; return to agent_node
[13] Call LLM | model_call=2 | state_message_types='HumanMessage, AIMessage, ToolMessage'
[14] LLM returned final answer
[15] No tool call -> route agent -> END
[16] LangGraph finished
[17] Request finished | model_calls=2 | elapsed_ms=...
```

`[03]` 的“Bind tool schema”不是把 Python 文件上传给模型，而是把 `read_file` 的名字、参数 `path: str` 和用途提供给模型 API。模型第一次调用只产生“我要调用 read_file”的结构化意图；`[10]` 才是本机 Python 真正读取文件；第二次模型调用才看得到 ToolMessage 中的文件内容并生成答案。

## 面试怎么说

我先用一个同步 JSON 接口跑通最小 Agent 主链。FastAPI 只负责输入输出，LangGraph 负责状态和节点跳转，节点调用 OpenAI-compatible 模型；模型不需要工具时直接结束，需要工具时才进入 ToolNode 并回到模型。
