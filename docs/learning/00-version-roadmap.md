# CodePilot 版本路线：每次只多学一层

当前项目已完成 V3。下面的 V0 到 V1.1 是为了让你理解“当前结构比上一版多了什么”，不是说仓库保留了多套并行代码。

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

## V2：SSE Agent 过程事件流

```text
User → POST /api/chat/stream → SSE status
→ LangGraph Agent Loop → SSE tool_call / tool_result
→ SSE answer → SSE done
```

新增：标准 `text/event-stream` 响应、`status`、`tool_call`、`tool_result`、`answer`、`done` 事件，以及请求级 LLM 调用计数。V2 流式返回节点完成事件和最终答案，**不实现逐 Token 输出**；当前 Agent Node 仍使用同步 `invoke()`，这样可以先看清 Agent Loop，再单独学习异步 Token Streaming。

## V3：Coding Agent 最小修改闭环，当前版本

```text
Requirement → Search / Read → Propose Patch → Human Approval → Run Tests
```

新增：`search_code`、`propose_patch`、`run_tests`，以及 `POST /api/changes/{change_id}/approve`。Patch 先在内存中生成并经人工批准；测试工具只运行固定 pytest 命令。

## 后续版本，当前不实现

| 版本 | 只计划学习什么 |
| --- | --- |
| V4 | Code RAG：Chunk、Embedding、Top-K、Token Budget |
| V5 | 持久化 Thread/Message、最小 Main + Branch 双栏 UI、Anchor 与独立 Branch Context |

数据库不在 V2-V4 过早加入。它只在 V5 的多请求会话和 Branch 必须保存时引入；学习版先使用 SQLite，理解表、外键和查询后，再讨论 PostgreSQL。Anchor Branch 也放在 V5：它需要后端保存 `main_message_id + anchor`，也需要前端让用户选中文本、打开/关闭 Branch，因此会以最小双栏页面和后端语义一起实现。

当前不要把 V4 以上的能力写进简历或当作已实现功能。
