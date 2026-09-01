# 06 V4：从零理解 Hybrid Code RAG

本章只讲当前 CodePilot 已实现的 V4，不把计划能力说成已完成。

## 1. 先理解 RAG 解决什么

RAG 不是把整个仓库塞给模型，而是先找少量相关代码，再作为背景交给模型：

```text
Task → Chunk → Retrieval → Top-K → Token Budget → Context → Agent
```

模型不知道本地仓库；直接发送整个仓库会增加 Token、延迟和无关上下文，也可能超过上下文窗口。V3 的 `search_code` 是模型主动调用的精确工具；V4 Retrieval 在模型第一次思考前自动提供候选背景，两者可以同时使用。

当前调用链：

```text
api/chat.py::retrieve_context
→ HybridCodeRetriever.retrieve(message)
→ build_context(results)
→ build_agent_graph(..., retrieved_context)
→ nodes.py 将 context 拼入 SystemMessage
→ DeepSeek
```

SSE 会先发：

```text
event: retrieval
data: {"result_count": 3, "context_chars": 842}
```

这只是候选数量和最终上下文字符数，不是 Recall@K 或正确率。

## 2. Chunk：当前怎样切代码

实现是 `backend/app/retrieval/retriever.py::_chunks()`。当前只扫描 workspace 下的 `*.py`，用 Python 标准库 `ast.parse()` 找顶层 `FunctionDef`、`AsyncFunctionDef`、`ClassDef`。

每个 Chunk 有：

```text
path / start_line / end_line / text / symbol
```

例如 `refund_order()` 会成为一个函数级 Chunk，`symbol="refund_order"`。没有顶层 Symbol 或 AST 解析失败时，整文件作为一个 Chunk。

当前限制必须背清楚：只支持 Python；不解析 Go/Java/TS Symbol；顶层 import、全局变量可能不在函数 Chunk 中；没有调用图、重叠滑窗或增量索引。

## 3. 三种检索信号

Query 和代码会先转小写、把下划线和标点拆开、去重。例如：

```text
refund_order() → {refund, order}
```

### lexical

比较 Query Token 与 `path + text` 的交集：

```text
lexical = 命中的唯一 Query Token 数 / Query Token 总数
```

它擅长函数名、错误码、配置键等精确词；不擅长同义词。

### symbol

只比较 Query Token 与函数/类名：

```text
symbol = 命中的唯一 Query Token 数 / Query Token 总数
```

它强调“代码职责名称”，避免某个词只在无关注释中出现就被排前。

### semantic

Embedding 将 Query 和 Chunk 映射为向量，当前用余弦相似度：

```text
cos(q,d) = (q · d) / (||q|| × ||d||)
```

它补充词面不一致的情况。只有明确配置：

```env
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=
```

才会调用 OpenAI-compatible Embedding Provider。未配置、文档向量化失败或查询向量化失败时，`semantic=0`，`reason` 标记 `semantic unavailable`，主 Agent 仍按 lexical + symbol 工作。DeepSeek Chat Key 不会被错误当作 Embedding 服务。

## 4. Hybrid Fusion、Top-K、Token Budget

当前可解释的初始融合公式：

```text
final_score = 0.5 × lexical + 0.3 × symbol + 0.2 × semantic
```

这不是行业标准或调优后的最佳权重。它表达当前偏好：精确文本最重要，Symbol 其次，语义作补充。真实项目应根据固定任务集调参。

排序后取 Top-K，当前默认：

```text
top_k = 4
```

K 太小会漏关键代码（Recall 低）；K 太大引入无关内容（Precision 低、Token 高）。因此 K 不是越大越好。

`build_context(..., token_budget=800)` 再做第二层限制。它按分数顺序追加 Chunk，以：

```text
Token ≈ 字符数 / 4
```

近似扣预算。预算不足时不再加入后续 Chunk；单个 Chunk 太长时只取前段。它避免整个仓库无脑注入，但不是官方 tokenizer 精确计数，也可能截断函数尾部。

## 5. 当前测试真实验证什么

`tests/test_v4_retrieval.py` 有两组测试。

第一组构造 `payment.py::refund_order`、`other.py::unrelated` 和 Query `how does refund work`；使用 `FakeEmbedder`，断言 `payment.py` 排第一、symbol 为 `refund_order`、reason 同时包含 lexical/symbol/semantic。这验证融合与排序，不是远程 Embedding 质量。

第二组不传 Embedder，Query 为 `validate token`，预算为 `20`；断言仍有结果、reason 含 `semantic unavailable`、Context 长度受限。这验证降级与预算边界。

当前没有：真实 Embedding Smoke Test、真实仓库 Recall@K、答案正确率、延迟成本压测或向量数据库性能测试。因此不能在简历虚填指标。

## 6. 项目当前的固定任务集与真实基线

任务集在 `evals/codepilot_retrieval_v1.json`，不是由被评模型临时出题：12 个任务都标注了真实源码证据 `expected_files` 和 `expected_symbols`。其中 8 个是用于调整 K/预算的 `dev`，4 个是最后才看的 `holdout`。

运行命令：

```bash
uv run python -m app.evals.retrieval_eval \
  --workspace . \
  --dataset evals/codepilot_retrieval_v1.json \
  --output evals/reports/codepilot_retrieval_v1_lexical.json \
  --top-k 4 --token-budget 800
```

当前未配置 Embedding 的真实基线报告为：12 个任务、文件级 Recall@4 `0.75`、Symbol 级 Recall@4 `0.75`、平均 Context `3199` 字符。它只代表这个小型项目内任务集的 lexical+symbol 基线，不能外推为通用 RAG 能力，也没有测量 Agent 最终答案正确率。

## 7. 高频面试问答

### RAG 与 Function Calling 有何区别？

RAG 在模型调用前自动筛选背景，解决“模型一开始该看什么”；Function Calling 是模型推理后主动请求精确操作。CodePilot 用 RAG 给初始候选上下文，用 Tool 做继续核实、读文件、提案和测试。

### 为什么 Hybrid，不只做向量检索？

代码中的路径、函数名、错误码是强精确特征，lexical/symbol 往往比语义向量稳定；语义检索补充同义表达。两者互补，向量不是天然更高级。

### Top-K 怎么选？

当前 4 是小型仓库初始值，不宣称最优。正确做法是在固定任务集比较 K=2/4/8 的 Recall@K、答案正确率和 Prompt Token，在正确率满足时选 Token 更低的 K。

### 为什么暂时不用 Milvus、Elasticsearch、pgvector？

当前小 workspace 用进程内 Chunk 列表足以证明链路。向量数据库解决大规模持久化、ANN 和并发，不是 RAG 的必要条件；V4 每次仍会扫描和向量化，适合学习而非大仓库生产。

### 当前最重要的边界是什么？

> 我实现的是小型 Python 代码仓的轻量 Hybrid Retrieval：函数/类级 Chunk，lexical、symbol、可选 semantic 融合，Top-K 和近似 Token Budget。Embedding 不可用时自动降级。它不是向量数据库、GraphRAG，也没有真实 Recall@K 指标；后续要用固定任务集和向量索引完成评测。
