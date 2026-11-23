"""Every model call goes through one guard: it retries in the open, limits rate and concurrency, keeps a run budget, and stops loops.

Observability shows; this regulates. Each attempt is its own span, so a retried 429 is never hidden inside one slow success.
The SDKs are set to retry nothing themselves.

Limits come from env vars (defaults in Limits): WARRANT_MAX_ATTEMPTS, WARRANT_RPS, WARRANT_MAX_CONCURRENCY, WARRANT_BREAKER_THRESHOLD,
WARRANT_RUN_MAX_CALLS, WARRANT_RUN_MAX_USD, WARRANT_TRACE_MAX_CALLS, WARRANT_REPEAT_MAX.
"""
import collections
import hashlib
import os
import random
import threading
import time
from dataclasses import dataclass, fields

from opentelemetry import trace

tracer = trace.get_tracer("warrant.callguard")


class GuardError(RuntimeError):
    """The guard refused or gave up on a call. Callers fail closed: the gate holds."""


class CircuitOpen(GuardError):
    pass


class BudgetExceeded(GuardError):
    pass


class LoopDetected(GuardError):
    pass


RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504, 529}
FATAL = {401, 402, 403}    # bad key, no balance, suspended: stop the run, never retry


@dataclass
class Limits:
    max_attempts: int = 3
    base_backoff: float = 1.0
    max_backoff: float = 30.0
    rps: float = 2.0
    max_concurrency: int = 4
    breaker_threshold: int = 5
    run_max_calls: int = 2000
    run_max_usd: float = 5.0
    trace_max_calls: int = 12
    repeat_max: int = 3

    @classmethod
    def from_env(cls):
        out = {}
        for f in fields(cls):
            v = os.getenv(f"WARRANT_{f.name.upper()}")
            if v is not None:
                out[f.name] = type(f.default)(v)
        return cls(**out)


def status_of(e):
    """HTTP status and Retry-After from any SDK's error, or (None, None) for a network failure."""
    status = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
    headers = getattr(getattr(e, "response", None), "headers", None) or {}
    ra = headers.get("retry-after") if hasattr(headers, "get") else None
    try:
        ra = float(ra) if ra is not None else None
    except ValueError:
        ra = None
    return status, ra


class Guard:
    def __init__(self, limits=None, sleep=time.sleep):
        self.limits = limits or Limits.from_env()
        self.sleep = sleep
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(self.limits.max_concurrency)
        self.next_slot = 0.0
        self.failures = 0
        self.open_reason = None
        self.per_trace = collections.Counter()
        self.repeats = collections.Counter()
        self.totals = collections.Counter()

    def _pace(self):
        """A simple token bucket: no more than rps calls start per second, across threads."""
        if self.limits.rps <= 0:
            return
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next_slot)
            self.next_slot = start + 1.0 / self.limits.rps
        if start > now:
            self.sleep(start - now)

    def _admit(self, prompt):
        ctx = trace.get_current_span().get_span_context()
        tid = f"{ctx.trace_id:032x}" if ctx.trace_id else None
        key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        with self.lock:
            if self.open_reason:
                self.totals["refused_open"] += 1
                raise CircuitOpen(f"circuit open: {self.open_reason}")
            if self.totals["calls"] >= self.limits.run_max_calls:
                raise BudgetExceeded(f"run call budget of {self.limits.run_max_calls} reached")
            if self.totals["usd"] >= self.limits.run_max_usd:
                raise BudgetExceeded(f"run spend budget of ${self.limits.run_max_usd:.2f} reached (${self.totals['usd']:.4f})")
            if tid:
                if self.per_trace[tid] >= self.limits.trace_max_calls:
                    self.totals["loops"] += 1
                    raise LoopDetected(f"{self.per_trace[tid]} model calls already in this trace")
                if self.repeats[(tid, key)] >= self.limits.repeat_max:
                    self.totals["loops"] += 1
                    raise LoopDetected(f"the same prompt sent {self.repeats[(tid, key)]} times in this trace")
                self.per_trace[tid] += 1
                self.repeats[(tid, key)] += 1
            self.totals["calls"] += 1
        return key

    def _trip(self, reason):
        with self.lock:
            self.open_reason = self.open_reason or reason
            self.totals["breaker_trips"] += 1

    def call(self, provider, prompt, fn, span):
        """Run fn() under the limits. fn returns the provider's raw result or raises the SDK's error."""
        key = self._admit(prompt)
        span.set_attribute("llm.prompt_hash", key)
        last = None
        for attempt in range(1, self.limits.max_attempts + 1):
            self._pace()
            with self.slots, tracer.start_as_current_span("llm.attempt") as a:
                a.set_attribute("llm.attempt", attempt)
                a.set_attribute("llm.provider", provider)
                try:
                    out = fn()
                    a.set_attribute("http.response.status_code", 200)
                    with self.lock:
                        self.failures = 0
                    span.set_attribute("llm.retry_count", attempt - 1)
                    return out
                except GuardError:
                    raise
                except Exception as e:
                    status, ra = status_of(e)
                    a.set_attribute("http.response.status_code", status or 0)
                    a.set_attribute("error.type", type(e).__name__)
                    if ra is not None:
                        a.set_attribute("http.retry_after_s", ra)
                    a.set_status(trace.Status(trace.StatusCode.ERROR, str(e)[:200]))
                    last = e
            with self.lock:
                self.failures += 1
                self.totals["failed_attempts"] += 1
                if status == 429:
                    self.totals["rate_limited"] += 1
            span.set_attribute("llm.retry_count", attempt)
            if status in FATAL:
                self._trip(f"provider returned {status}; check the key and balance")
                raise CircuitOpen(f"provider returned {status}; not retried") from last
            if self.failures >= self.limits.breaker_threshold:
                self._trip(f"{self.failures} failed attempts in a row, last status {status}")
            if status is not None and status not in RETRYABLE:
                raise GuardError(f"provider returned {status}; not retryable") from last
            if self.open_reason:
                raise CircuitOpen(f"circuit open: {self.open_reason}") from last
            if attempt < self.limits.max_attempts:
                with self.lock:
                    self.totals["retries"] += 1
                wait = ra if ra is not None else min(self.limits.max_backoff, self.limits.base_backoff * 2 ** (attempt - 1))
                self.sleep(wait * (1 + 0.1 * random.random()) if wait else 0)
        raise GuardError(f"gave up after {self.limits.max_attempts} attempts") from last

    def spend(self, usd, tokens_in, tokens_out):
        with self.lock:
            self.totals["usd"] += usd
            self.totals["tokens_in"] += tokens_in
            self.totals["tokens_out"] += tokens_out

    def summary(self):
        t = dict(self.totals)
        t["usd"] = round(t.get("usd", 0.0), 4)
        t["circuit_open"] = self.open_reason
        return t


GUARD = Guard()
