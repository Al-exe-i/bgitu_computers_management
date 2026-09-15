"""Composition and resource lifecycle for operational commands."""

from contextlib import asynccontextmanager
from functools import partial

from core.redis_client import close_cache_redis
from db.bootstrap_lock import PostgresBootstrapLock
from db.post_commit import add_post_commit_hook, clear_post_commit_hooks
from db.session import engine, session_factory
from db.transaction import SessionTransaction
from dependencies.cache import (
    get_analytics_filter_options_cache,
    get_office_short_list_cache,
    get_user_cache,
)
from modules.administration.application.bootstrap import BootstrapUseCase
from modules.identity.repositories.sessions import UserSessionRepository
from modules.identity.repositories.users import UserRepository
from modules.identity.services.management import ManagedUserService
from modules.inventory.repositories.bootstrap import OfficeBootstrapRepository
from modules.inventory.services.bootstrap import OfficeBootstrapService


def build_managed_users(session) -> ManagedUserService:
    return ManagedUserService(
        UserRepository(session),
        UserSessionRepository(session),
        get_user_cache(),
        on_commit=partial(add_post_commit_hook, session),
    )


def build_bootstrap(session) -> BootstrapUseCase:
    def invalidate_offices():
        add_post_commit_hook(session, get_office_short_list_cache().invalidate)
        add_post_commit_hook(session, get_analytics_filter_options_cache().invalidate)

    return BootstrapUseCase(
        build_managed_users(session),
        OfficeBootstrapService(
            OfficeBootstrapRepository(session), on_changed=invalidate_offices
        ),
        PostgresBootstrapLock(session),
    )


@asynccontextmanager
async def managed_session():
    async with session_factory() as session:
        try:
            yield session
        except BaseException:
            clear_post_commit_hooks(session)
            await session.rollback()
            raise
        else:
            await SessionTransaction(session).commit()


async def close_runtime() -> None:
    try:
        await close_cache_redis()
    finally:
        await engine.dispose()
