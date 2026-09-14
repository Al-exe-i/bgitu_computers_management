from sqlalchemy.ext.asyncio import AsyncSession

from db.post_commit import clear_post_commit_hooks, run_post_commit_hooks


class SessionTransaction:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        try:
            await self.session.commit()
        except BaseException:
            clear_post_commit_hooks(self.session)
            await self.session.rollback()
            raise
        await run_post_commit_hooks(self.session)
