import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from models import UsedRefreshToken, User, UserSession
from modules.identity.public import UserRole
from modules.identity.repositories.sessions import UserSessionRepository


class AsyncSessionFacade:
    """Exercise repository SQL against an isolated SQLite DB without network I/O."""

    def __init__(self, session):
        self.session = session

    async def execute(self, statement):
        return self.session.execute(statement)

    def add(self, value):
        self.session.add(value)

    async def flush(self):
        self.session.flush()


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
    User.metadata.create_all(
        engine,
        tables=[User.__table__, UserSession.__table__, UsedRefreshToken.__table__],
    )
    with Session(engine) as session:
        user = User(email="user@example.ru", password="hash", role=UserRole.teacher)
        session.add(user)
        session.flush()
        session.add(
            UserSession(
                user_id=user.id,
                sid="sid-1",
                refresh_token_hash="original-hash",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        session.commit()
        yield session
    engine.dispose()


def test_rotation_remembers_all_consumed_hashes_and_cleanup_cascades(db):
    async def scenario():
        repo = UserSessionRepository(AsyncSessionFacade(db))
        for old, new in [
            ("original-hash", "second-hash"),
            ("second-hash", "third-hash"),
        ]:
            assert await repo.rotate_refresh_token_hash(
                sid="sid-1", old_hash=old, new_hash=new
            )
            db.commit()

        for old in ["original-hash", "second-hash"]:
            assert await repo.get_active_by_refresh_token_hash(old) is None
            assert (
                await repo.get_active_by_used_refresh_token_hash(old)
            ).sid == "sid-1"
        assert (
            await repo.get_active_by_refresh_token_hash("third-hash")
        ).sid == "sid-1"

        assert not await repo.rotate_refresh_token_hash(
            sid="sid-1", old_hash="unknown", new_hash="bad"
        )
        assert db.get(UsedRefreshToken, "unknown") is None

        await repo.revoke("sid-1")
        assert await repo.get_active_by_used_refresh_token_hash("original-hash") is None

        db.delete(db.scalar(select(UserSession)))
        db.commit()
        assert db.scalars(select(UsedRefreshToken)).all() == []

    asyncio.run(scenario())


def test_failed_transaction_does_not_consume_refresh_token(db):
    async def scenario():
        repo = UserSessionRepository(AsyncSessionFacade(db))
        assert await repo.rotate_refresh_token_hash(
            sid="sid-1", old_hash="original-hash", new_hash="new-hash"
        )
        db.rollback()
        assert await repo.get_active_by_refresh_token_hash("original-hash") is not None
        assert await repo.get_active_by_used_refresh_token_hash("original-hash") is None

    asyncio.run(scenario())


def test_expired_session_is_not_treated_as_active_refresh_reuse(db):
    async def scenario():
        repo = UserSessionRepository(AsyncSessionFacade(db))
        assert await repo.rotate_refresh_token_hash(
            sid="sid-1", old_hash="original-hash", new_hash="new-hash"
        )
        session = db.scalar(select(UserSession))
        session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
        assert await repo.get_active_by_used_refresh_token_hash("original-hash") is None
        assert not await repo.rotate_refresh_token_hash(
            sid="sid-1", old_hash="new-hash", new_hash="bad"
        )

    asyncio.run(scenario())


def test_revoke_by_owner_does_not_modify_refresh_history(db):
    async def scenario():
        repo = UserSessionRepository(AsyncSessionFacade(db))
        session = db.scalar(select(UserSession))
        assert not await repo.revoke_by_sid_and_user(session.sid, session.user_id + 1)
        assert await repo.revoke_by_sid_and_user(session.sid, session.user_id)
        assert not await repo.revoke_by_sid_and_user(session.sid, session.user_id)
        assert db.scalars(select(UsedRefreshToken)).all() == []

    asyncio.run(scenario())
