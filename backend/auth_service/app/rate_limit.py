import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self):
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()

        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] >= window_seconds:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = max(
                    1,
                    int(window_seconds - (now - bucket[0])),
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)


limiter = InMemoryRateLimiter()


def limit_requests(action: str, max_requests: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        client_host = request.client.host if request.client else "unknown"
        limiter.hit(
            key=f"{action}:{client_host}",
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    return dependency
