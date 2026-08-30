# CodePilot Agent development notes

This is an independent learning project. Do not edit sibling repositories from
this directory. Keep the implementation small and source-traceable: every
feature must have a test, a documented request flow, and a clear distinction
between model reasoning and deterministic side effects.

The intended stack is Python, FastAPI, LangGraph, local retrieval, typed tools,
an isolated workspace, and SSE. Do not add DeerFlow runtime abstractions unless
the user explicitly asks to compare or reuse a narrowly scoped implementation.

V1 is intentionally smaller: JSON `POST /api/chat`, one StateGraph, one
workspace-scoped `read_file` Tool, and tests that assert the complete message
sequence. Keep diagrams under `docs/learning/assets/` as PNG files with editable
Mermaid sources beside them; do not require a Mermaid plugin to read learning docs.

`CODEPILOT_DEBUG` is a teaching feature. Each request trace must record a
request ID, StateGraph progression, message types, LLM call count, tool summary
and duration without emitting API keys, authentication headers, complete prompts,
or unbounded tool output. Keep `/health` independent of model settings so
learners can verify FastAPI before configuring a provider.
