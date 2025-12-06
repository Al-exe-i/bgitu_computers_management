# app/db/session.py
from typing import AsyncGenerator, Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.config import settings
from db.listeners import setup_listeners

engine = create_async_engine(
    settings.db.url,
    echo=False, #Settings.DEBUG
)

session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

setup_listeners()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


session_dep = Annotated[AsyncSession, Depends(get_db)]
