"""Shared rate limiter for API clients."""

from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_calls: int, period: float = 60.0) -> None:
        self.max_calls = max_calls
        self.period = period
        self._ts: deque[float] = deque()

    def wait(self) -> None:
        now = time.time()
        while self._ts and now - self._ts[0] >= self.period:
            self._ts.popleft()
        if len(self._ts) >= self.max_calls:
            time.sleep(self.period - (now - self._ts[0]) + 0.05)
        self._ts.append(time.time())
