from modules.identity.contracts import UserSummary
from modules.identity.repositories.users import UserRepository


class UserSummaryReader:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_summaries(self, user_ids: set[int]) -> dict[int, UserSummary]:
        return await self.repo.get_summaries(user_ids)
