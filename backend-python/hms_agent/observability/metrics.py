"""Agent metrics.

Deliberately small and dependency-free. The brief suggested OpenTelemetry, and
that is the right destination — but OTel is only useful with a collector to ship
to, and this deployment has none yet. Adding the SDK now would add dependencies
and produce nothing observable.

So this records the same shapes OTel uses (counters, histograms, per-run spans)
behind an interface that maps onto it directly. `export_otel_spans()` marks the
seam: when a collector exists, that is the only function that changes.

Percentiles are computed over a bounded window, so memory does not grow with
traffic.
"""
from __future__ import annotations

import math
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any

#: Keep at most this many latency samples per key.
WINDOW = 2048


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile. Returns 0.0 for an empty sample."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


@dataclass
class RunSpan:
    """One agent run, shaped like a trace span."""

    run_id: str
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    user_id: str | None = None
    role: str | None = None
    outcome: str | None = None
    tool_calls: int = 0
    policy_blocks: int = 0
    approvals: int = 0
    retries: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> int:
        end = self.ended_at if self.ended_at is not None else time.time()
        return int((end - self.started_at) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "role": self.role,
            "outcome": self.outcome,
            "duration_ms": self.duration_ms,
            "tool_calls": self.tool_calls,
            "policy_blocks": self.policy_blocks,
            "approvals": self.approvals,
            "retries": self.retries,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "events": self.events,
        }


class MetricsRegistry:
    """Thread-safe counters, latency windows and run spans."""

    def __init__(self, window: int = WINDOW):
        self._lock = threading.Lock()
        self._counters: Counter = Counter()
        self._latencies: dict[str, deque] = {}
        self._spans: dict[str, RunSpan] = {}
        self._completed: deque = deque(maxlen=window)
        self._window = window

    # -- counters ---------------------------------------------------------

    def increment(self, name: str, amount: int = 1, **labels: Any) -> None:
        with self._lock:
            self._counters[self._key(name, labels)] += amount

    def observe_latency(self, name: str, milliseconds: float, **labels: Any) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._latencies.setdefault(key, deque(maxlen=self._window)).append(milliseconds)

    @staticmethod
    def _key(name: str, labels: dict) -> str:
        if not labels:
            return name
        rendered = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{rendered}}}"

    # -- spans ------------------------------------------------------------

    def start_run(self, run_id: str, user_id: str | None = None, role: str | None = None) -> RunSpan:
        span = RunSpan(run_id=run_id, user_id=user_id, role=role)
        with self._lock:
            self._spans[run_id] = span
        self.increment("agent_runs_started")
        return span

    def get_run(self, run_id: str) -> RunSpan | None:
        with self._lock:
            return self._spans.get(run_id)

    def record_event(self, run_id: str, event: str, **detail: Any) -> None:
        span = self.get_run(run_id)
        if span is None:
            return
        span.events.append({"event": event, "at": time.time(), **detail})

    def end_run(self, run_id: str, outcome: str) -> RunSpan | None:
        span = self.get_run(run_id)
        if span is None:
            return None
        span.ended_at = time.time()
        span.outcome = outcome
        with self._lock:
            self._completed.append(span)
            self._spans.pop(run_id, None)
        self.increment("agent_runs_completed", outcome=outcome)
        self.observe_latency("agent_run_duration_ms", span.duration_ms)
        return span

    # -- reporting --------------------------------------------------------

    def counter(self, name: str, **labels: Any) -> int:
        with self._lock:
            return self._counters.get(self._key(name, labels), 0)

    def latency(self, name: str, p: float = 50.0, **labels: Any) -> float:
        with self._lock:
            samples = list(self._latencies.get(self._key(name, labels), []))
        return percentile(samples, p)

    def snapshot(self) -> dict[str, Any]:
        """The dashboard view. Every figure is measured, never estimated."""
        with self._lock:
            completed = list(self._completed)
            counters = dict(self._counters)
            durations = list(self._latencies.get("agent_run_duration_ms", []))

        total = len(completed)
        succeeded = sum(1 for s in completed if s.outcome == "COMPLETE")
        escalated = sum(1 for s in completed if s.outcome in ("ESCALATE", "EXHAUSTED"))
        denied = sum(1 for s in completed if s.outcome == "DENIED")
        tool_calls = sum(s.tool_calls for s in completed)
        cost = sum(s.cost_usd for s in completed)

        return {
            "runs": total,
            "succeeded": succeeded,
            "escalations": escalated,
            "denied": denied,
            "success_rate": round(succeeded / total, 4) if total else 0.0,
            "avg_tool_calls": round(tool_calls / total, 2) if total else 0.0,
            "latency_p50_ms": round(percentile(durations, 50)),
            "latency_p95_ms": round(percentile(durations, 95)),
            "total_cost_usd": round(cost, 4),
            "avg_cost_usd": round(cost / total, 6) if total else 0.0,
            "policy_blocks": sum(s.policy_blocks for s in completed),
            "counters": counters,
        }

    def export_otel_spans(self) -> list[dict[str, Any]]:
        """The seam.

        Returns completed runs in a span-like shape. When a collector exists,
        this is the only function that needs to change — the call sites that
        record metrics do not.
        """
        with self._lock:
            return [s.to_dict() for s in self._completed]


#: Per-1M-token prices, filled in from the provider's published rates at the
#: time of measurement. Left empty rather than guessed: a cost figure derived
#: from an invented rate is worse than no cost figure.
TOKEN_PRICES_USD_PER_MILLION: dict[str, dict[str, float]] = {}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Cost in USD, or 0.0 when the model's price is not configured.

    Returning 0.0 for an unknown model is intentional: the dashboard then shows
    a cost of zero, which reads as "not measured", rather than a plausible
    number nobody can trace to a rate card.
    """
    price = TOKEN_PRICES_USD_PER_MILLION.get(model)
    if not price:
        return 0.0
    return (
        prompt_tokens / 1_000_000 * price.get("input", 0.0)
        + completion_tokens / 1_000_000 * price.get("output", 0.0)
    )
