# 03 Tool Calling：模型、框架、我的代码三层分别做什么

## 概念是什么

Function Calling 不是模型执行 Python。模型只返回结构化意图，例如：

```text
name = "read_file"
args = {"path": "note.txt"}
```

程序收到这个 `AIMessage.tool_calls` 后，才会决定是否真的执行对应函数。

## 为什么需要 Tool

模型训练时不知道你的本地 workspace 文件。`read_file` 给它一条受限制的读取通道：它能请求一个相对路径，但不能读取宿主机任意文件。

## 三层边界

### 1. 模型 Function Calling

`graph.py::build_agent_graph()` 的 `model.bind_tools([read_file])` 把 Tool schema 交给 OpenAI-compatible Chat Model。模型在 `nodes.py::agent()` 的 `bound_model.invoke()` 中返回 AIMessage，是否包含 `tool_calls` 完全由模型决定。

### 2. LangChain / LangGraph Tool Runtime

`ToolNode([read_file])` 是框架执行器。`route_after_agent()` 选择 `tools` 时，ToolNode 读取 AIMessage 的 tool_calls，校验参数，调用 Tool，并把返回值包装成 ToolMessage。图上的 `tools → agent` Edge 会让携带 ToolMessage 的 State 重新进入模型。

### 3. 项目自己的 Python read_file

[backend/app/tools/read_file.py](../../backend/app/tools/read_file.py) 的 `build_read_file_tool()` 用 `@tool("read_file")` 定义 schema 和实际函数。函数调用 [workspace/manager.py](../../backend/app/workspace/manager.py) 的 `resolve_workspace_file()`：拒绝绝对路径和 `..`，确认解析后的路径仍在 workspace root 下，只读取普通文件，并限制最大返回字符数。

## 真实顺序

```text
HumanMessage
→ agent Node 调 LLM
→ AIMessage.tool_calls
→ route_after_agent 返回 "tools"
→ ToolNode 调 read_file(path)
→ ToolMessage(content=file contents)
→ agent Node 再调 LLM
→ AIMessage(final answer)
```

## 异常怎么处理

`../../outside.txt` 在 `resolve_workspace_file()` 被拒绝，原因是路径含有 `..`。不存在的文件也会得到明确 ValueError。V1 没有错误恢复策略，ToolNode 的异常会使调用失败；这是下一阶段可以单独学习的错误处理话题，不要说已经实现模型自动恢复。

## 面试怎么说

模型只生成 tool_call。LangGraph ToolNode 负责把 tool_call 路由为 ToolMessage；我实现的是唯一的 `read_file` 工具和 workspace 路径边界，确保模型不能直接读取任意宿主机文件。
