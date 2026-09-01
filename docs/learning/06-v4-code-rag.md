# 06 V4：轻量 Hybrid Code RAG

V4 在每次 Agent 调用前执行：

```text
Task → Python symbol chunks → lexical + symbol + optional semantic score
→ Top-K → Token Budget → Retrieved code context → Agent
```

实现位于 `backend/app/retrieval/retriever.py`。Python 文件用 AST 切分顶层函数和类，Chunk 包含路径、行号、文本和 symbol。`HybridCodeRetriever` 融合三类分数：代码文本/路径关键词、函数或类名命中、可选 Embedding cosine 相似度。

语义检索通过 `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL` 显式配置 OpenAI-compatible Embedding Provider。未配置或调用失败时，系统不会失败，而是记录 `semantic unavailable` 并退回 lexical + symbol；当前 DeepSeek Chat Key 不会被假装成 Embedding 服务。

`build_context()` 以约 `字符数 / 4` 估算 Token，按 Top-K 顺序截断，避免把整个仓库无脑放进 Prompt。当前索引是每请求在内存构建，适合小仓库，不是向量数据库。

SSE 会新增：

```text
event: retrieval
data: {"result_count": ..., "context_chars": ...}
```

面试表述：我先用轻量 Hybrid Code Retrieval 从小型 workspace 中筛选函数级代码块，融合 lexical、symbol 和可选 semantic 信号，并以 Token Budget 组织上下文；Embedding 不可用时自动降级，当前不把该实现表述为向量数据库或 GraphRAG。
