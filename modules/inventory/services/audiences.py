from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from core.exceptions import AudienceAlreadyExistsError, AudienceNotFoundError
from modules.inventory.models.audience import Audience
from modules.inventory.repositories.audiences import AudienceRepository
from modules.inventory.schemas.analytics import HardwareAnalyticsFilterOptions
from modules.inventory.schemas.audience import (
    AudienceCreate,
    AudienceResponse,
    AudienceShortResponse,
    AudienceUpdate,
)
from modules.inventory.schemas.office import OfficeShort
from modules.inventory.services.audience_landmarks import normalize_landmarks
from modules.inventory.services.cache import AfterCommit, invalidate_after_commit
from modules.inventory.services.grid import AudienceGridService
from services.response_cache import RedisTypedCache


class AudienceService:
    def __init__(
        self,
        repo: AudienceRepository,
        grid: AudienceGridService,
        office_short_cache: RedisTypedCache[list[OfficeShort]] | None = None,
        analytics_filter_options_cache: RedisTypedCache[HardwareAnalyticsFilterOptions]
        | None = None,
        *,
        on_commit: AfterCommit | None = None,
    ):
        self.repo = repo
        self.grid = grid
        self.on_commit = on_commit
        self.office_short_cache = office_short_cache
        self.analytics_filter_options_cache = analytics_filter_options_cache

    async def get_list(self) -> Sequence[AudienceResponse]:
        audiences = await self.repo.get_all()
        return [
            AudienceResponse.model_validate(a, from_attributes=True) for a in audiences
        ]

    async def get_one(self, audience_id: int) -> AudienceResponse:
        audience = await self.repo.get_by_id(audience_id)
        if not audience:
            raise AudienceNotFoundError()
        return AudienceResponse.model_validate(audience, from_attributes=True)

    async def get_one_by_public_id(self, public_id: UUID) -> AudienceResponse:
        audience = await self.repo.get_by_public_id(public_id)
        if not audience:
            raise AudienceNotFoundError()
        return AudienceResponse.model_validate(audience, from_attributes=True)

    async def create_audience(self, schema: AudienceCreate) -> AudienceShortResponse:
        self.grid.validate(schema.hardware, schema.width, schema.height)

        audience_data = schema.model_dump(exclude={"hardware"})

        audience_orm = Audience(
            **audience_data,
            hardware=self.grid.build_hardware_models(schema.hardware),
        )

        try:
            created = await self.repo.create(audience_orm)
        except IntegrityError as exc:
            raise AudienceAlreadyExistsError() from exc
        self._invalidate_related_caches_after_commit()
        return AudienceShortResponse.model_validate(created, from_attributes=True)

    async def update_audience(
        self, audience_id: int, schema: AudienceUpdate
    ) -> AudienceShortResponse:
        current_audience = await self.repo.get_by_id(audience_id)
        if not current_audience:
            raise AudienceNotFoundError()

        return await self._update_existing_audience(current_audience, schema)

    async def update_audience_by_public_id(
        self, public_id: UUID, schema: AudienceUpdate
    ) -> AudienceShortResponse:
        current_audience = await self.repo.get_by_public_id(public_id)
        if not current_audience:
            raise AudienceNotFoundError()

        return await self._update_existing_audience(current_audience, schema)

    async def delete_audience(self, audience_id: int) -> None:
        await self.get_one(audience_id)
        await self.repo.delete(audience_id)
        self._invalidate_related_caches_after_commit()

    async def delete_audience_by_public_id(self, public_id: UUID) -> None:
        audience = await self.repo.get_one_short_by_public_id(public_id)
        if not audience:
            raise AudienceNotFoundError()

        await self.repo.delete(audience.id)
        self._invalidate_related_caches_after_commit()

    async def _update_existing_audience(
        self, current_audience: Audience, schema: AudienceUpdate
    ) -> AudienceShortResponse:
        audience_id = current_audience.id
        update_data = schema.model_dump(exclude_unset=True, exclude={"hardware"})
        moved = any(
            key in update_data and update_data[key] != getattr(current_audience, key)
            for key in ("office_id", "floor")
        )

        if "landmarks" in update_data:
            update_data["landmarks"] = normalize_landmarks(update_data["landmarks"])

        target_width = update_data.get("width", current_audience.width)
        target_height = update_data.get("height", current_audience.height)

        if schema.hardware is not None:
            self.grid.validate(schema.hardware, target_width, target_height)

        if update_data:
            for key, value in update_data.items():
                setattr(current_audience, key, value)
            try:
                await self.repo.flush()
            except IntegrityError as exc:
                raise AudienceAlreadyExistsError() from exc

        if schema.hardware is not None:
            await self.grid.sync(audience_id, schema.hardware)

        if moved:
            await self.repo.remove_floor_placement(current_audience.public_id)
        await self.repo.flush()
        updated = await self.repo.get_by_id(audience_id)
        self._invalidate_related_caches_after_commit()
        return AudienceShortResponse.model_validate(updated, from_attributes=True)

    def _invalidate_related_caches_after_commit(self) -> None:
        invalidate_after_commit(
            self.on_commit,
            self.office_short_cache,
            self.analytics_filter_options_cache,
        )
