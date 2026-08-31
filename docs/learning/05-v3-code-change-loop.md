# 05 V3：从读取代码到人工确认的修改闭环

## V3 新增的目标

V1/V2 只能让模型读取文件并回答。V3 把它扩展为一个最小、可审查的 Coding Agent 闭环：

```text
需求
→ search_code / read_file / run_tests
→ LLM 分析
→ propose_patch
→ 人工检查 Diff
→ POST approve
→ run_tests
```

关键边界是：模型不能直接改文件。它只能创建一个 `pending_approval` 的 Patch 提案；真正写入必须由用户调用单独的批准 API。

## 新增的四个 Tool

| Tool | 做什么 | 安全边界 |
| --- | --- | --- |
| `search_code(query, max_results)` | 小型代码仓内按路径和文本行进行大小写无关检索 | 只扫描 workspace 中至多 200 个常见文本文件，最多返回 10 行 |
| `read_file(path)` | 读取已定位文件 | 只能读取 workspace 下的相对路径 |
| `propose_patch(path, expected_text, replacement_text)` | 创建统一 Diff 和待批准提案 | 不写文件；旧文本必须恰好出现一次 |
| `run_tests()` | 运行 workspace 测试 | 只能执行固定的 `python -m pytest -q`，无任意 shell 参数 |

`search_code` 是 V3 的 lexical search，不是 RAG：它没有 Embedding、向量索引或语义召回。这些明确留给 V4。

## Patch 为什么分成提案和批准

`propose_patch` 的工作是：

```text
读取原文件
→ 验证 expected_text 恰好出现一次
→ 在内存中生成 proposed_content 和 unified diff
→ 分配 change_id
→ 返回 pending_approval
```

此时磁盘文件不变。用户通过：

```text
POST /api/changes/{change_id}/approve
```

才会真正写入。批准前还会再次比较当前文件内容和提案时的原内容：若文件已被别人修改，提案变为 `stale` 并拒绝写入。这避免旧 Diff 覆盖新修改。

V3 的提案保存在 Python 进程内存中，进程重启后会丢失；这是当前刻意的限制。V5 才将 Thread、Message、Branch 等跨请求数据放进 SQLite。

## Agent 调用一次还是多次模型

这取决于模型的决策，不固定。一次真实 V3 修复任务可能是：

```text
model_call=1
→ 同时请求 read_file(calculator.py) 和 search_code("def add")

model_call=2
→ 继续 search_code("add")

model_call=3
→ 请求 propose_patch(...)

model_call=4
→ 根据 ToolMessage 说明提案和 change_id
```

一个 `AIMessage` 可以含多个 `tool_calls`。ToolNode 会执行这一批已请求工具，得到对应的多个 ToolMessage；随后 Agent 再调用模型。日志中的 `tool_call_count` 和 `tools=[...]` 会显示这件事。

## 亲手验证

启动服务：

```bash
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

创建提案，注意先记录 SSE 中的 `change_id`：

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"请检查 demo/calculator.py 中 add 函数导致测试失败的问题。必须先搜索或读取相关代码；确认最小修改后调用 propose_patch 创建修复提案。不要声称已经修改文件。"}'
```

应该看见：

```text
tool_call: read_file / search_code
tool_call: propose_patch
tool_result: status=pending_approval, change_id=...
answer: 尚未修改，等待批准
```

查看 Diff：

```bash
curl http://127.0.0.1:8000/api/changes/你的change_id
```

确认 Diff 正确后才批准：

```bash
curl -X POST http://127.0.0.1:8000/api/changes/你的change_id/approve
```

最后让 Agent 使用固定测试工具验证：

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"请运行 workspace 测试验证刚才批准的 calculator 修复；必须调用 run_tests，并报告 exit_code。"}'
```

`workspace/demo/calculator.py` 是故意有 Bug 的已跟踪演示文件。完成实验后可恢复到初始 Bug，方便下次重复：

```bash
git restore workspace/demo/calculator.py
```

## 面试怎么说

> V3 在基础 Tool Calling 之上实现了最小 Coding Agent 修改闭环：Agent 先通过受限 lexical search 和文件读取定位代码，再由 `propose_patch` 产生带 change_id 的统一 Diff。该 Tool 只生成内存提案，不直接写盘；用户经独立批准 API 确认后，服务端会再次校验源文件未变化才应用修改。测试工具也不接收任意 shell 命令，只允许在 workspace 中执行固定 pytest 命令。当前检索仍是 lexical，不把它表述为 RAG。
