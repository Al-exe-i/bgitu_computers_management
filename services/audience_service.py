from typing import Sequence

from sqlalchemy.exc import IntegrityError

from core.exceptions import AudienceAlreadyExistsError, AudienceNotFoundError
from models import Audience
from repositories.audience_repo import AudienceRepository
from schemas.audience import AudienceCreate, AudienceUpdate, AudienceResponse
from services.audience_grid_service import AudienceGridService
from utils.audience_landmarks import normalize_landmarks


class AudienceService:
    def __init__(self, repo: AudienceRepository, grid: AudienceGridService):
        self.repo = repo
        self.grid = grid

    async def get_list(self) -> Sequence[AudienceResponse]:
        audiences = await self.repo.get_all()
        return [
            AudienceResponse.model_validate(a, from_attributes=True)
            for a in audiences
        ]

    async def get_one(self, audience_id: int):
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            raise AudienceNotFoundError()
        return audience

    async def create_audience(self, schema: AudienceCreate):
        self.grid.validate(schema.hardware, schema.width, schema.height)

        audience_data = schema.model_dump(exclude={'hardware'})

        audience_orm = Audience(
            **audience_data,
            hardware=self.grid.build_hardware_models(schema.hardware),
        )

        try:
            return await self.repo.create(audience_orm)
        except IntegrityError as exc:
            raise AudienceAlreadyExistsError() from exc

    async def update_audience(self, audience_id: int, schema: AudienceUpdate):
        current_audience = await self.repo.get_by_id(audience_id)
        if not current_audience:
            raise AudienceNotFoundError()

        update_data = schema.model_dump(exclude_unset=True, exclude={'hardware'})

        if "landmarks" in update_data:
            update_data["landmarks"] = normalize_landmarks(update_data["landmarks"])

        target_width = update_data.get("width", current_audience.width)
        target_height = update_data.get("height", current_audience.height)

        if schema.hardware is not None:
            self.grid.validate(schema.hardware, target_width, target_height)

        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            await self.repo.flush()

        if schema.hardware is not None:
            await self.grid.sync(audience_id, schema.hardware)

        await self.repo.flush()
        return await self.repo.get_by_id(audience_id)

    async def delete_audience(self, audience_id: int) -> None:
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)
