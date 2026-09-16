from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from taskiq import TaskiqEvents, TaskiqState

from core.config import settings
from modules.identity.models.user_session import UserSession
from taskiq_app import broker

# Один пул на event loop воркера; закрывается при его остановке.
_engine = None
_session_factory = None


def _get_session_factory() -> async_sessionmaker:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_async_engine(
            str(settings.db.url),
            echo=False,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
        )
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def open_task_session() -> AsyncIterator[AsyncSession]:
    async with _get_session_factory()() as session:
        yield session


async def _cleanup_user_sessions_async(retention_days: int) -> dict:
    if isinstance(retention_days, bool) or not isinstance(retention_days, int) or retention_days < 0:
        raise ValueError("retention_days must be a non-negative integer")
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=retention_days)

    async with open_task_session() as session:
        # удаляем истёкшие (expires_at < now)
        res_expired = await session.execute(
            delete(UserSession).where(UserSession.expires_at < now)
        )

        # удаляем revoked старше cutoff
        res_revoked_old = await session.execute(
            delete(UserSession).where(
                UserSession.revoked_at.is_not(None),
                UserSession.revoked_at < cutoff,
            )
        )

        await session.commit()

        # rowcount может быть -1 на некоторых драйверах, но на Postgres обычно норм
        return {
            "expired_deleted": res_expired.rowcount,
            "revoked_deleted": res_revoked_old.rowcount,
            "retention_days": retention_days,
        }


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def close_task_database(state: TaskiqState) -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


@broker.task(
    task_name="tasks.sessions.cleanup_user_sessions",
    schedule=[{"cron": "10 3 * * *", "args": [7]}],
)
async def cleanup_user_sessions(retention_days: int = 7) -> dict:
    result = await _cleanup_user_sessions_async(retention_days)
    logger.info("Очистка пользовательских сессий завершена: {}", result)
    return result
