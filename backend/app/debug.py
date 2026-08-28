"""Small opt-in teaching logs for following one V1 request in a terminal."""

from __future__ import annotations

import os
from typing import Any


def debug_enabled() -> bool:
    return os.getenv("CODEPILOT_DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}


def debug_log(step: int, message: str, **details: Any) -> None:
    """Print concise, secret-safe flow markers only when learning mode is enabled."""

    if not debug_enabled():
        return
    suffix = "" if not details else " | " + " | ".join(f"{key}={value!r}" for key, value in details.items())
    print(f"[CodePilot][{step:02d}] {message}{suffix}", flush=True)
