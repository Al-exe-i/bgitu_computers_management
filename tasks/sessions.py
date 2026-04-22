import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from celery_app import celery_app
from core.config import settings
from models.user_session import UserSession


def _make_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        str(settings.db.url),
        echo=False,
        pool_pre_ping=True,
    )
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def _cleanup_user_sessions_async(retention_days: int) -> dict:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)

    session_factory = _make_sessionmaker()

    async with session_factory() as session:
        # 1) удаляем истёкшие (expires_at < now)
        res_expired = await session.execute(
            delete(UserSession).where(UserSession.expires_at < now)
        )

        # 2) удаляем revoked старше cutoff
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


@celery_app.task(name="tasks.sessions.cleanup_user_sessions")
def cleanup_user_sessions(retention_days: int = 7) -> dict:
    """
    Celery task: cleanup user sessions.
    - deletes expired sessions
    - deletes revoked sessions older than retention_days
    """
    result = asyncio.run(_cleanup_user_sessions_async(retention_days))
    print(f"[cleanup_user_sessions] {result}")
    return result
