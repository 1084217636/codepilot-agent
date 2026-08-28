# CodePilot 版本路线：每次只多学一层

当前项目处于 V1.2。下面的 V0 到 V1.1 是为了让你理解“当前结构比上一版多了什么”，不是说仓库保留了多套并行代码。

## V0：项目骨架

```text
README / AGENTS / gitignore
```

学习目标：Git 项目、依赖文件、环境变量不提交。

## V0.1：FastAPI 最小服务

```text
User → FastAPI → Response
```

当前证据：`backend/app/main.py::health()`，`GET /health` 返回 `{"status":"ok"}`。它不进入 LangGraph，也不调用 LLM。

## V1.0：普通 LLM Chat

```text
User → FastAPI → LLM → Answer
```

当前的“无 Tool Call”分支就是这个结构：`POST /api/chat` 创建 HumanMessage，Agent Node 调用 LLM，`route_after_agent()` 发现没有 `tool_calls` 后结束。

学习点：模型 API、HumanMessage、AIMessage、环境变量模型配置。

## V1.1：LangGraph 单节点

```text
User → FastAPI → StateGraph → agent Node → LLM → Answer
```

当前证据：`state.py::AgentState`、`nodes.py::make_agent_node`、`graph.py::build_agent_graph`。这版新增 State、Node、Edge、compile、invoke。

## V1.2：Tool Calling Agent，当前版本

```text
User → FastAPI → LangGraph → Agent → LLM
→ tool_call → read_file → ToolMessage
→ Agent → LLM → Answer
```

新增：`tools/read_file.py`、`model.bind_tools`、`ToolNode`、`route_after_agent` 条件边、workspace 路径边界、教学日志。

## 以后，但本轮不实现

| 版本 | 只计划学习什么 |
| --- | --- |
| V1.3 | Streaming / SSE |
| V2 | search_code、apply_patch、run_test、人工确认 |
| V3 | Code RAG：Chunk、Embedding、Top-K |
| V4 | History、Checkpoint、Summary、Token Budget |
| V5 | 从旧项目迁移 Anchor、Branch 与 Main Context 语义 |

当前不要把 V2 以上的能力写进简历或当作已实现功能。
