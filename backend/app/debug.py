"""Small opt-in teaching logs for following one V1 request in a terminal."""

from __future__ import annotations

import os
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class RequestTrace:
    """Mutable request facts shared by LangGraph's nested execution contexts."""

    request_id: str
    started_at: float
    model_calls: int = 0


_trace: ContextVar[RequestTrace | None] = ContextVar("codepilot_trace", default=None)


def debug_enabled() -> bool:
    return os.getenv("CODEPILOT_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}


def begin_trace(request_id: str | None = None) -> RequestTrace:
    """Start one request-local teaching trace and reset its model-call counter."""

    trace_id = request_id or uuid4().hex[:8]
    trace = RequestTrace(request_id=trace_id, started_at=time.perf_counter())
    _trace.set(trace)
    return trace


def activate_trace(trace: RequestTrace) -> None:
    """Make an existing request trace active in a resumed SSE generator context."""

    _trace.set(trace)


def _current_trace() -> RequestTrace:
    """Return the active trace, or create a deterministic one for direct graph tests."""

    trace = _trace.get()
    if trace is None:
        trace = RequestTrace(request_id="no-request", started_at=time.perf_counter())
        _trace.set(trace)
    return trace


def next_model_call() -> int:
    """Increment and return the number of LLM invocations in this request."""

    trace = _current_trace()
    trace.model_calls += 1
    return trace.model_calls


def trace_summary() -> dict[str, int | str]:
    """Return safe request-level facts for the final teaching log line."""

    trace = _current_trace()
    elapsed_ms = round((time.perf_counter() - trace.started_at) * 1_000)
    return {
        "request_id": trace.request_id,
        "model_calls": trace.model_calls,
        "elapsed_ms": elapsed_ms,
    }


def debug_log(step: int, message: str, **details: Any) -> None:
    """Print concise, secret-safe flow markers only when learning mode is enabled."""

    if not debug_enabled():
        return
    safe_details = {"request_id": _current_trace().request_id, **details}
    suffix = " | " + " | ".join(f"{key}={value!r}" for key, value in safe_details.items())
    print(f"[CodePilot][{step:02d}] {message}{suffix}", flush=True)
