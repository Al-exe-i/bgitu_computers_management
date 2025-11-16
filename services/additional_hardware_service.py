from fastapi import HTTPException
from repositories.additional_hardware_repo import AdditionalHardwareRepository
from schemas.additional_hardware import AdditionalHardwareCreate, AdditionalHardwareUpdate, AdditionalHardwareRead


class AdditionalHardwareService:

    def __init__(self, repo: AdditionalHardwareRepository):
        self.repo = repo

    async def create_hardware(self, data: AdditionalHardwareCreate) -> AdditionalHardwareRead:
        hardware_orm = await self.repo.create(data)
        return AdditionalHardwareRead.model_validate(hardware_orm)

    async def get_hardware_by_audience(self, audience_id: int) -> list[AdditionalHardwareRead]:
        hardware_list = await self.repo.get_by_audience(audience_id)
        return [
            AdditionalHardwareRead.model_validate(item)
            for item in hardware_list
        ]

    async def update_hardware(self, hardware_id: int, data: AdditionalHardwareUpdate) -> AdditionalHardwareRead | None:
        hardware = await self.repo.get(hardware_id)
        if not hardware:
            raise HTTPException(status_code=404, detail="Hardware not found")

        orm_model = await self.repo.update(hardware, data)

        return AdditionalHardwareRead.model_validate(orm_model)

    async def delete_hardware(self, hardware_id: int) -> bool:
        hardware = await self.repo.get(hardware_id)
        if not hardware:
            return False

        await self.repo.delete(hardware)
        return True

    async def delete_all_hardware(self, audience_id: int) -> int:
        return await self.repo.delete_all_for_audience(audience_id)