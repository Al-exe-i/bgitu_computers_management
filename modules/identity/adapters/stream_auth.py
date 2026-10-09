import asyncio
import time
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from db import session as db_session
from modules.identity.repositories.users import UserRepository


@dataclass(frozen=True, slots=True)
class StreamAuthorization:
    user_id: int
    token_version: int
    expires_at: float

    @property
    def check_interval(self) -> float:
        return max(0.01, min(5.0, self.expires_at - time.time()))

    async def rejection_reason(self) -> str | None:
        if time.time() >= self.expires_at:
            return "expired"
        try:
            # Never keep a DB connection for the lifetime of a stream.
            async with asyncio.timeout(2):
                async with db_session.session_factory() as session:
                    version = await UserRepository(session).get_access_token_version(
                        self.user_id
                    )
        except (SQLAlchemyError, OSError, TimeoutError):
            logger.warning(
                "SSE authorization check unavailable for user_id={}", self.user_id
            )
            return "unavailable"
        if time.time() >= self.expires_at:
            return "expired"
        return None if version == self.token_version else "revoked"
