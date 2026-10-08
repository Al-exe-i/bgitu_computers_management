from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

PostRollbackHook = Callable[[], Any | Awaitable[Any]]

_POST_ROLLBACK_HOOKS_KEY = "post_rollback_hooks"


def add_post_rollback_hook(session: AsyncSession, hook: PostRollbackHook) -> None:
    session.info.setdefault(_POST_ROLLBACK_HOOKS_KEY, []).append(hook)


def clear_post_rollback_hooks(session: AsyncSession) -> None:
    session.info.pop(_POST_ROLLBACK_HOOKS_KEY, None)


async def run_post_rollback_hooks(session: AsyncSession) -> None:
    hooks = list(session.info.pop(_POST_ROLLBACK_HOOKS_KEY, []))
    for hook in hooks:
        try:
            result = hook()
            if inspect.isawaitable(result):
                await result
        except Exception:  # noqa: BLE001 - cleanup must not hide the transaction error
            logger.exception(
                "Post-rollback hook failed: {}",
                getattr(hook, "__qualname__", repr(hook)),
            )
