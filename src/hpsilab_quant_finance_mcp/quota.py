"""Process-local burst protection for downstream SDK requests."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

# The per-minute ceiling the hosted API applies to anonymous and Free callers.
# Held locally so a runaway agent loop is stopped here instead of ten HTTP
# requests later. A refusal at this boundary clears itself inside a minute,
# which is the only reason a local guess about a remote limit is safe to make.
LOCAL_REQUESTS_PER_MINUTE = 10


@dataclass(frozen=True, slots=True)
class RateLimited:
    """Describe the local burst boundary that refused a request."""

    limit: int
    window: str
    retry_after_seconds: float
    reset_at: str
    tool: str | None = None


class BurstRateLimiter:
    """Enforce a per-minute request ceiling without retaining raw API keys.

    Day-scoped gates used to live here too: 100 requests per UTC day and 20
    per tool per day. They mirrored the requests-per-day quotas the hosted API
    retired on 2026-08-08, when Credits became the unit of entitlement — and
    they mirrored them in the one place that can see neither a balance nor a
    plan. A Developer key (60 rpm) or a Pro key (300 rpm, 15,000 Credits) was
    refused here at the Free tier's numbers, for the rest of the UTC day,
    without a request ever leaving the process.

    What remains is burst protection and nothing else. It guards the hosted
    API from a loop; it does not pretend to meter entitlement, because
    entitlement now has one authority and it is not this process.
    """

    def __init__(
        self,
        *,
        wall_time: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._wall_time = wall_time
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._minute_requests: dict[str, deque[float]] = defaultdict(deque)

    def check_and_consume(self, api_key: str, tool: str) -> RateLimited | None:
        """Consume one request allowance or return the blocking limit."""
        identity = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        now_wall = self._wall_time()
        now_monotonic = self._monotonic()

        with self._lock:
            minute_requests = self._minute_requests[identity]
            while minute_requests and now_monotonic - minute_requests[0] >= 60.0:
                minute_requests.popleft()

            if len(minute_requests) >= LOCAL_REQUESTS_PER_MINUTE:
                retry_after = max(0.0, 60.0 - (now_monotonic - minute_requests[0]))
                return RateLimited(
                    limit=LOCAL_REQUESTS_PER_MINUTE,
                    window="minute",
                    retry_after_seconds=retry_after,
                    reset_at=self._reset_at(now_wall, retry_after),
                    tool=tool,
                )

            minute_requests.append(now_monotonic)
            return None

    def _reset_at(self, now: float, retry_after_seconds: float) -> str:
        reset = datetime.fromtimestamp(now + retry_after_seconds, timezone.utc)
        return reset.isoformat(timespec="seconds").replace("+00:00", "Z")
