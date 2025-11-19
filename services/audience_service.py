from functools import cache
from db.listeners import OFFICE_AUDIENCE_RULES
from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceRead, AudienceCreateRequest, AudienceUpdate, AudienceBase


class AudienceService:

    def __init__(self, repo: AudienceRepository):
        self.repo = repo

    async def get_all(self, lazy=False) -> list[AudienceRead]:
        response_model = AudienceRead
        if lazy:
            audiences = await self.repo.get_all_lazy()
            response_model = AudienceBase
        else:
            audiences = await self.repo.get_all()
        return [response_model.model_validate(a, from_attributes=True) for a in audiences]

    async def get(self, aud_id: int) -> AudienceRead | None:
        audience_orm = await self.repo.get(aud_id)
        if not audience_orm:
            return None
        return AudienceRead.model_validate(audience_orm, from_attributes=True)

    async def get_available_for_creation(self) -> list[int]:
        existing_audiences = await self.get_all(lazy=True)
        existing_ids = {audience.id for audience in existing_audiences}
        return sorted(self.__get_all_possible_audiences() - existing_ids)

    async def create(self, data: AudienceCreateRequest) -> AudienceRead:
        audience_orm = await self.repo.create(data)
        return AudienceRead.model_validate(audience_orm, from_attributes=True)

    async def update(self, audience_id: int, data: AudienceUpdate) -> AudienceRead | None:
        audience = await self.repo.get(audience_id)
        if not audience:
            return None
        updated = await self.repo.update(audience, data)
        return AudienceRead.model_validate(updated, from_attributes=True)

    async def delete(self, aud_id: int) -> bool:
        audience = await self.repo.get(aud_id)

        if audience:
            await self.repo.delete(audience)
            return True

        return False

    @cache
    def __get_all_possible_audiences(self) -> set[int]:
        return OFFICE_AUDIENCE_RULES.get(1, frozenset()) | OFFICE_AUDIENCE_RULES.get(2, frozenset())

