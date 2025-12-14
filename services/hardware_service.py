from core.exceptions import HTTP404
from repositories.hardware_repo import HardwareRepository
from schemas.hardware import HardwareUpdate


class HardwareService:
    def __init__(self, repo: HardwareRepository):
        self.repo = repo

    async def update_status(self, hardware_id: int, schema: HardwareUpdate):
        update_data = schema.model_dump(exclude_unset=True)

        updated_hw = await self.repo.update(hardware_id, update_data)
        if not updated_hw:
            raise HTTP404("Hardware not found")
        return updated_hw