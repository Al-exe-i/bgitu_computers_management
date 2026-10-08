from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from db.post_commit import clear_post_commit_hooks, run_post_commit_hooks
from db.post_rollback import clear_post_rollback_hooks, run_post_rollback_hooks


class SessionTransaction:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        try:
            await self.session.flush()
        except BaseException:
            await self._rollback_after_failure()
            raise

        try:
            await self.session.commit()
        except BaseException as exc:
            # COMMIT may have succeeded despite a lost reply or cancellation.
            clear_post_commit_hooks(self.session)
            clear_post_rollback_hooks(self.session)
            logger.warning(
                "Commit outcome is unknown after {}; transaction hooks discarded",
                type(exc).__name__,
            )
            await self._rollback_after_failure()
            raise
        clear_post_rollback_hooks(self.session)
        await run_post_commit_hooks(self.session)

    async def rollback(self) -> None:
        clear_post_commit_hooks(self.session)
        try:
            await self.session.rollback()
        finally:
            await run_post_rollback_hooks(self.session)

    async def _rollback_after_failure(self) -> None:
        try:
            await self.rollback()
        except BaseException:
            logger.exception("Rollback failed while handling a transaction error")
