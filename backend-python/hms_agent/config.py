"""Runtime configuration for the cutover.

One switch decides which pipeline serves tool calls, so the guarded path can be
enabled in development and staging before it becomes the only path in
production.
"""
from __future__ import annotations

import os
from enum import Enum


class ToolExecutionMode(str, Enum):
    #: The shipped pipeline: no authentication, reflective dispatch.
    LEGACY = "legacy"
    #: Both pipelines run; the guarded decision is recorded but the legacy result
    #: is returned. For collecting a live comparison without changing behaviour.
    SHADOW = "shadow"
    #: Authenticated, registry-resolved, schema-validated, policy-gated.
    GUARDED = "guarded"

    @classmethod
    def current(cls) -> "ToolExecutionMode":
        raw = (os.getenv("TOOL_EXECUTION_MODE") or "legacy").strip().lower()
        try:
            return cls(raw)
        except ValueError:
            raise RuntimeError(
                f"TOOL_EXECUTION_MODE={raw!r} is not one of "
                f"{[m.value for m in cls]}"
            )


def guarded_enabled() -> bool:
    return ToolExecutionMode.current() is ToolExecutionMode.GUARDED
