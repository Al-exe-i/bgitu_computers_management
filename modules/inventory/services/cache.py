from collections.abc import Awaitable, Callable
from typing import Protocol

AfterCommit = Callable[[Callable[[], Awaitable[None]]], None]


class InvalidateCache(Protocol):
    async def invalidate(self) -> None: ...


def invalidate_after_commit(
    schedule: AfterCommit | None, *caches: InvalidateCache | None
) -> None:
    for cache in caches:
        if cache is None:
            continue
        after_commit(schedule, cache.invalidate)


def after_commit(
    schedule: AfterCommit | None, callback: Callable[[], Awaitable[None]]
) -> None:
    if schedule is None:
        raise ValueError("Inventory cache requires a post-commit scheduler")
    schedule(callback)
