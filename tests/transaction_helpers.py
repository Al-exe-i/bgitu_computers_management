from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock

from db.post_commit import add_post_commit_hook
from db.post_rollback import add_post_rollback_hook


def make_transaction_session():
    return SimpleNamespace(
        info={}, flush=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock()
    )


def transaction_callbacks(session):
    return {
        "on_commit": partial(add_post_commit_hook, session),
        "on_rollback": partial(add_post_rollback_hook, session),
    }
