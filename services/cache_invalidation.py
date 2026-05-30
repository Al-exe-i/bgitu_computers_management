from typing import Protocol

from db.post_commit import add_post_commit_hook


class InvalidateCache(Protocol):
    async def invalidate(self) -> None: ...


def invalidate_after_commit(source: object, *caches: InvalidateCache | None) -> None:
    session = getattr(source, "db", None) or getattr(source, "session", None)
    if session is None:
        return

    for cache in caches:
        if cache is None:
            continue
        add_post_commit_hook(session, cache.invalidate)
