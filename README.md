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

当前只完成项目隔离与初始化，尚未实现 Agent、RAG、工具调用或 SSE。功能范围以后续需求文档为准。
