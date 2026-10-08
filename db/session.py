# db/session.py
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import db.base  # noqa: F401 -- register models before any session is used
from core.config import settings
from db.transaction import SessionTransaction

engine = create_async_engine(
    str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_pre_ping=True,
)

session_factory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        except BaseException:
            await SessionTransaction(session).rollback()
            raise
        else:
            await SessionTransaction(session).commit()


# Finish writes and release connections before sending responses, including SSE.
session_dep = Annotated[AsyncSession, Depends(get_db, scope="function")]
