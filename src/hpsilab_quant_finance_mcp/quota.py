"""Process-local Free-tier quota enforcement for downstream SDK requests."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

FREE_REQUESTS_PER_DAY = 100
FREE_REQUESTS_PER_MINUTE = 10
FREE_REQUESTS_PER_TOOL_PER_DAY = 20


@dataclass(frozen=True, slots=True)
class QuotaExceeded:
    """Describe the first local quota boundary that rejected a request."""

    limit: int
    window: str
    retry_after_seconds: float
    tool: str | None = None


class FreeTierQuotaLimiter:
    """Enforce Free SDK quotas without retaining raw API keys."""

    def __init__(
        self,
        *,
        wall_time: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._wall_time = wall_time
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._daily_totals: dict[tuple[str, str], int] = defaultdict(int)
        self._daily_tools: dict[tuple[str, str, str], int] = defaultdict(int)
        self._minute_requests: dict[str, deque[float]] = defaultdict(deque)
        self._active_day: str | None = None

    def check_and_consume(self, api_key: str, tool: str) -> QuotaExceeded | None:
        """Consume one request allowance or return the blocking quota."""
        identity = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        now_wall = self._wall_time()
        now_monotonic = self._monotonic()
        day = datetime.fromtimestamp(now_wall, timezone.utc).date().isoformat()

        with self._lock:
            self._reset_expired_days(day)
            minute_requests = self._minute_requests[identity]
            while minute_requests and now_monotonic - minute_requests[0] >= 60.0:
                minute_requests.popleft()

            if len(minute_requests) >= FREE_REQUESTS_PER_MINUTE:
                return QuotaExceeded(
                    limit=FREE_REQUESTS_PER_MINUTE,
                    window="minute",
                    retry_after_seconds=max(0.0, 60.0 - (now_monotonic - minute_requests[0])),
                )

            daily_key = (identity, day)
            if self._daily_totals[daily_key] >= FREE_REQUESTS_PER_DAY:
                return QuotaExceeded(
                    limit=FREE_REQUESTS_PER_DAY,
                    window="day",
                    retry_after_seconds=self._seconds_until_next_utc_day(now_wall),
                )

            tool_key = (identity, day, tool)
            if self._daily_tools[tool_key] >= FREE_REQUESTS_PER_TOOL_PER_DAY:
                return QuotaExceeded(
                    limit=FREE_REQUESTS_PER_TOOL_PER_DAY,
                    window="day",
                    retry_after_seconds=self._seconds_until_next_utc_day(now_wall),
                    tool=tool,
                )

            minute_requests.append(now_monotonic)
            self._daily_totals[daily_key] += 1
            self._daily_tools[tool_key] += 1
            return None

    def _reset_expired_days(self, day: str) -> None:
        if self._active_day == day:
            return
        self._daily_totals.clear()
        self._daily_tools.clear()
        self._active_day = day

    def _seconds_until_next_utc_day(self, now: float) -> float:
        current = datetime.fromtimestamp(now, timezone.utc)
        next_day = datetime.combine(current.date() + timedelta(days=1), datetime.min.time(), timezone.utc)
        return max(0.0, (next_day - current).total_seconds())
