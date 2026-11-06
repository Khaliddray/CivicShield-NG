"""In-memory sliding-window IP rate limiter for API endpoint defense."""

import time
import threading
from typing import Dict, List, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter per client IP."""

    def __init__(self) -> None:
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_ip: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int]:
        """Check if request is allowed under sliding window limit."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            timestamps = self._requests.get(client_ip, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]
            if len(valid_timestamps) >= limit:
                retry_after = int(valid_timestamps[0] - cutoff) + 1
                self._requests[client_ip] = valid_timestamps
                return False, max(1, retry_after)
            valid_timestamps.append(now)
            self._requests[client_ip] = valid_timestamps
            return True, 0

    def cleanup(self, max_age_seconds: int = 300) -> None:
        """Evict stale client IP entries."""
        now = time.time()
        cutoff = now - max_age_seconds
        with self._lock:
            stale_ips = [ip for ip, ts in self._requests.items() if not ts or ts[-1] < cutoff]
            for ip in stale_ips:
                del self._requests[ip]


rate_limiter = SlidingWindowRateLimiter()

# Endpoint specific rate limits: path -> (max_requests, window_seconds)
# Generous limits for testing/development while protecting against DDoS
RATE_LIMIT_POLICIES = {
    "/api/v1/auth/login": (100, 60),
    "/api/v1/auth/register": (60, 60),
    "/api/v1/reports": (100, 60),
    "/api/v1/voice/transcribe": (60, 60),
}
