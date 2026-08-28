# CodePilot Agent development notes

This is an independent learning project. Do not edit sibling repositories from
this directory. Keep the implementation small and source-traceable: every
feature must have a test, a documented request flow, and a clear distinction
between model reasoning and deterministic side effects.

The intended stack is Python, FastAPI, LangGraph, local retrieval, typed tools,
an isolated workspace, and SSE. Do not add DeerFlow runtime abstractions unless
the user explicitly asks to compare or reuse a narrowly scoped implementation.
