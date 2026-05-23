from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession


PostCommitHook = Callable[[], Any | Awaitable[Any]]

_POST_COMMIT_HOOKS_KEY = "post_commit_hooks"


def add_post_commit_hook(session: AsyncSession, hook: PostCommitHook) -> None:
    hooks = session.info.setdefault(_POST_COMMIT_HOOKS_KEY, [])
    hooks.append(hook)


def clear_post_commit_hooks(session: AsyncSession) -> None:
    session.info.pop(_POST_COMMIT_HOOKS_KEY, None)


async def run_post_commit_hooks(session: AsyncSession) -> None:
    hooks = list(session.info.pop(_POST_COMMIT_HOOKS_KEY, []))

    for hook in hooks:
        try:
            result = hook()
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("Post-commit hook failed: {}", _hook_name(hook))


def _hook_name(hook: PostCommitHook) -> str:
    return getattr(hook, "__qualname__", repr(hook))
