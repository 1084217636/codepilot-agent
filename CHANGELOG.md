# Changelog

## V1.2：Tool Calling Agent，当前版本

新增：

- `read_file` Tool、`model.bind_tools`、`ToolNode`、条件 Edge。
- `workspace/demo/README.md` 与 `hello.py` 示例。
- `CODEPILOT_DEBUG` 教学日志，显示 HumanMessage、AIMessage、ToolMessage 相关步骤。

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
