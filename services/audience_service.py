from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceRead, AudienceCreateRequest, AudienceUpdate


class AudienceService:

    def __init__(self, repo: AudienceRepository):
        self.repo = repo

    async def get_all(self) -> list[AudienceRead]:
        audiences = await self.repo.get_all()
        return [AudienceRead.model_validate(a, from_attributes=True) for a in audiences]

    async def get_by_id(self, aud_id: int) -> AudienceRead:
        audience_orm = await self.repo.get_by_id(aud_id)
        return AudienceRead.model_validate(audience_orm, from_attributes=True)

    async def create(self, data: AudienceCreateRequest) -> AudienceRead:
        audience_orm = await self.repo.create(data)
        return AudienceRead.model_validate(audience_orm, from_attributes=True)

    async def update(self, audience_id: int, data: AudienceUpdate) -> AudienceRead | None:
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            return None
        updated = await self.repo.update(audience, data)
        return AudienceRead.model_validate(updated, from_attributes=True)

    async def delete(self, aud_id: int) -> bool:
        audience = await self.repo.get_by_id(aud_id)

        if audience:
            await self.repo.delete(audience)
            return True

        return False

