"""Simple in-memory rate limiting for auth and OTP endpoints."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, DefaultDict, List

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Fixed-window rate limiter keyed by client identifier (e.g. IP)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, List[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds
        recent = [ts for ts in self._hits[key] if ts > window_start]
        if len(recent) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": self.window_seconds,
                },
            )
        recent.append(now)
        self._hits[key] = recent


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit_dependency(limiter: RateLimiter) -> Callable:
    async def _dependency(request: Request) -> None:
        limiter.check(client_ip(request))

    return _dependency


# Shared limiters — tune via env in config if needed
login_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
password_reset_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)
otp_rate_limiter = RateLimiter(max_requests=8, window_seconds=300)
