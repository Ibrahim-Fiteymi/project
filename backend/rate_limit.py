"""Simple in-memory token-bucket rate limiter keyed by client IP.

This is intentionally minimal — for production deploys behind a real proxy or
multi-worker setup, swap to slowapi or a Redis-backed limiter. For the MVP and
single-worker development, an in-process LRU is sufficient and adds no
infrastructure dependency.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque

from fastapi import HTTPException, Request


class IPRateLimiter:
    def __init__(self, *, max_calls: int, window_seconds: int) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._buckets: dict[str, Deque[float]] = {}
        self._lock = threading.Lock()
        # Periodic sweep so dormant IPs don't accumulate forever in a long-lived
        # process. Runs at most once per `_sweep_interval` seconds.
        self._sweep_interval = max(window_seconds, 60)
        self._last_sweep = time.monotonic()

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()
            self._last_sweep = time.monotonic()

    def _maybe_sweep_locked(self, now: float, cutoff: float) -> None:
        if now - self._last_sweep < self._sweep_interval:
            return
        for ip in [ip for ip, q in self._buckets.items() if not q or q[-1] < cutoff]:
            del self._buckets[ip]
        self._last_sweep = now

    def check(self, request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        cutoff = now - self.window
        with self._lock:
            self._maybe_sweep_locked(now, cutoff)
            bucket = self._buckets.setdefault(client, deque())
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_calls:
                retry_after = max(1, int(bucket[0] + self.window - now))
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Rate limit exceeded: {self.max_calls} requests per "
                        f"{self.window}s. Retry after {retry_after}s."
                    ),
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)
