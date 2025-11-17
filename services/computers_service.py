from repositories.computers_repo import ComputerRepository
from schemas.computer import ComputerRead, ComputerUpdate


class ComputerService:

    def __init__(self, repo: ComputerRepository):
        self.repo = repo

    async def update(self, computer_id: int, data: ComputerUpdate) -> ComputerRead | None:
        orm_model = await self.repo.get(computer_id)

        if not orm_model:
            return None

        result = await self.repo.update(orm_model, data)
        return ComputerRead.model_validate(result, from_attributes=True)