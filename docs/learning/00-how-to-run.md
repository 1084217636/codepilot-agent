# CodePilot V1.2：亲手启动与观察手册

本轮只需要两个终端。

```text
终端 1：启动 FastAPI，观察 [CodePilot][01] 到 [15] 日志
终端 2：用 curl 发 HTTP 请求
```

按顺序亲手操作。最后才运行 pytest。

## Step 1：进入项目

命令：

```bash
cd /home/xiaobin/myproject/codepilot-agent
```

正常看到什么：终端路径变成 `.../codepilot-agent`。

实际做什么：`cd` 只是进入项目目录，后续 `uv`、`.env`、`workspace` 都从这里找。

知识点：当前工作目录。

## Step 2：确认 Python

命令：

```bash
python3 --version
```

正常看到什么：Python 3.12 或更高版本。项目在 [pyproject.toml](../../pyproject.toml) 中要求 `>=3.12`。

实际做什么：确认解释器满足依赖版本。

知识点：Python Runtime。

## Step 3：创建环境与安装依赖

唯一推荐方案是 `uv`，不要同时自行选择 pip、Poetry 或 Conda。

命令：

```bash
uv sync --all-groups
```

正常看到什么：首次会创建 `.venv` 并安装 FastAPI、LangGraph、LangChain Core、langchain-openai、Pydantic、pytest。

实际做什么：`uv` 根据 `pyproject.toml` 和 `uv.lock` 创建项目隔离环境。之后运行命令统一写成 `uv run ...`，不需要手动 `source .venv/bin/activate`。

知识点：虚拟环境、依赖锁定。

## Step 4：配置模型 API

命令：

```bash
cp .env.example .env
```

打开 `.env`，填写真实值：

```env
MODEL_API_KEY=你的真实Key
MODEL_BASE_URL=你的OpenAI兼容接口地址
MODEL_NAME=你的模型名
CODEPILOT_DEBUG=true
CODEPILOT_WORKSPACE_ROOT=workspace
```

每个变量的作用：

- `MODEL_API_KEY`：模型服务认证，只放本机 `.env`，不能提交 Git。
- `MODEL_BASE_URL`：OpenAI-compatible API 根地址。
- `MODEL_NAME`：调用的模型标识。
- `CODEPILOT_DEBUG=true`：打开教学日志；改为 `false` 则不输出这些编号日志。
- `CODEPILOT_WORKSPACE_ROOT=workspace`：`read_file` 唯一能访问的根目录。

当前仓库不会复制或读取另一个 DeerFlow 项目的 Key。为 CodePilot 单独配置 Key，才能真正理解项目独立运行。

## Step 5：启动 FastAPI，终端 1

命令：

```bash
uv run uvicorn app.main:app --app-dir backend --reload --env-file .env
```

含义：

- `uvicorn`：ASGI Web Server。
- `app.main`：Python 模块 `backend/app/main.py`。
- `app`：该文件中的 FastAPI 实例。
- `--app-dir backend`：让 Python 能找到 `app` 包。
- `--reload`：改代码后开发服务器自动重启。
- `--env-file .env`：把本机模型配置加载进进程。

正常看到什么：类似 `Uvicorn running on http://127.0.0.1:8000`。此时没有调用模型。

知识点：ASGI、Uvicorn、FastAPI app。

## Step 6：health 检查，终端 2

命令：

```bash
curl http://127.0.0.1:8000/health
```

正常看到什么：

```json
{"status":"ok"}
```

实际做什么：只执行 `main.py::health()`，证明 HTTP 服务工作。它不进入 LangGraph，也不调用 LLM。

知识点：HTTP GET、健康检查。

## Step 7：发送普通 Chat，终端 2

命令：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好，请用一句话介绍你自己。"}'
```

PowerShell：

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/chat" -ContentType "application/json" -Body '{"message":"你好，请用一句话介绍你自己。"}'
```

正常看到什么：终端 2 收到 `{ "answer": "..." }`。终端 1 依次出现 `[01]` 到 `[08]`，其中 `[03] Enter LangGraph` 表示进入图，`[05] Calling LLM` 才是真正发起模型调用，`[07] No tool call -> finish` 表示这次不需要读文件。

实际做什么：HumanMessage 进入 `StateGraph`，agent Node 调模型，模型直接给最终 AIMessage。

知识点：POST JSON、HumanMessage、AIMessage、无 Tool 的图路径。

## Step 8：发送必须调用 read_file 的请求，终端 2

先确认示例文件存在：

```bash
cat workspace/demo/hello.py
```

再发送：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"请读取 demo/hello.py，告诉我 hello 函数返回什么。不要根据猜测回答，必须调用 read_file。"}'
```

注意：Tool 的路径相对于 workspace root，因此传 `demo/hello.py`，不是 `workspace/demo/hello.py`。

正常看到什么：终端 1 出现 `[01]` 到 `[15]`。关键观察点：

```text
[05] Calling LLM
[06] LLM returned tool_call | tool='read_file'
[07] Enter ToolNode
[08] Execute read_file
[09] read_file success
[10] ToolNode created ToolMessage
[11] Return to agent_node
[12] Calling LLM again
[13] LLM returned final answer
[14] LangGraph finished
[15] Return HTTP response
```

第一轮 LLM 不知道文件内容，只能请求 Tool；Python `read_file` 读取文件；ToolNode 把内容变成 ToolMessage；第二轮 LLM 看见 ToolMessage 后才组织自然语言答案。

知识点：Function Calling、ToolNode、ToolMessage、Agent Loop。

## Step 9：测试 Workspace 边界

通过 API 让模型传 `../` 不稳定，因为模型未必愿意按要求生成非法调用。此处直接运行 Tool 单测，最能稳定观察拒绝行为：

```bash
uv run pytest -v tests/test_read_file.py
```

正常看到什么：`test_read_file_rejects_path_escape PASSED`。

实际做什么：`resolve_workspace_file()` 发现路径含有 `..`，抛出 `ValueError("path must stay inside the workspace root")`。

知识点：路径穿越、最小权限。当前只是文件路径边界，不是容器级 Sandbox。

## Step 10：最后运行自动测试

命令：

```bash
uv run pytest -v
```

正常看到什么：5 项测试通过。

实际做什么：手工请求用于理解真实调用链；pytest 用于确认后续修改没有破坏 health、HTTP、Tool 边界和 Agent 消息序列。

知识点：手工验证与自动回归测试的区别。
