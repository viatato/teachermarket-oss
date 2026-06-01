from collections import defaultdict, deque
from time import monotonic
from typing import Callable

from fastapi import HTTPException, Request, status


_buckets: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(*, scope: str, limit: int, window_seconds: int) -> Callable[[Request], None]:
    async def dependency(request: Request) -> None:
        now = monotonic()
        bucket_key = f"{scope}:{client_ip(request)}"
        bucket = _buckets[bucket_key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Забагато запитів. Спробуйте трохи пізніше.",
            )
        bucket.append(now)

    return dependency
