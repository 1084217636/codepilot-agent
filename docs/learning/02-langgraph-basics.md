# 02 LangGraph：State、Node、Edge 在项目里各是什么

## 概念是什么

LangGraph 可以把 Agent 写成一张显式状态图：State 是每一步共同读写的数据，Node 是做事的函数，Edge 是下一步去哪里。

不用 LangGraph 时，你会自己写一个 `while True`：调用模型，判断有没有 tool_call，执行工具，把结果 append 到 messages，再调用模型。LangGraph 把这个循环变成可读的图结构。

## State 在哪里定义

[backend/app/agent/state.py](../../backend/app/agent/state.py) 的 `AgentState` 只有一个字段：`messages`。

`Annotated[list[AnyMessage], add_messages]` 的意思是：Node 返回的新消息追加到已有 State，而不是覆盖整个消息列表。

第一次调用图时 State 是：

```text
messages = [HumanMessage("请读取 note.txt")]
```

如果模型调用工具，最终 State 会变成：

```text
HumanMessage
→ AIMessage(tool_calls=[read_file])
→ ToolMessage(content="文件内容")
→ AIMessage(final answer)
```

## Node 在哪里定义

[backend/app/agent/nodes.py](../../backend/app/agent/nodes.py) 有两个关键函数：

- `make_agent_node(bound_model)`：返回真正的 `agent` Node。它把 `SYSTEM_PROMPT` 和 `state["messages"]` 交给 `bound_model.invoke()`，然后返回新 AIMessage。
- `route_after_agent(state)`：检查最新 AIMessage 的 `tool_calls`。有则返回 `tools`，没有则返回 `end`。

## Edge 和 compile 在哪里定义

[backend/app/agent/graph.py](../../backend/app/agent/graph.py) 的 `build_agent_graph()` 按顺序做了五件事：

1. 创建项目 Tool：`build_read_file_tool(workspace_root)`。
2. 调用 `model.bind_tools([read_file])`，让模型 API 知道可调用的 schema。
3. `StateGraph(AgentState)` 创建图。
4. 注册 `agent` Node 和 `ToolNode`。
5. 注册 `START → agent`、条件边 `agent → tools/END`、`tools → agent`，最后 `compile()`。

这就是 V1 最需要记住的源码位置。项目没有使用高层 `create_react_agent`，因为你需要看见 Node、Edge、compile、invoke 各自在哪。

## 面试怎么说

我用 StateGraph 显式定义最小 Agent Loop。State 只保存 messages，agent Node 调模型，条件边根据 AIMessage.tool_calls 决定结束还是进入 ToolNode，ToolNode 返回 ToolMessage 后再回到 agent Node。
