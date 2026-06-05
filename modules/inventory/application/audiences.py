from dataclasses import dataclass
from uuid import UUID

from schemas.audience import AudienceCreate, AudienceResponse, AudienceShortResponse, AudienceUpdate
from modules.inventory.events import AudienceUpdatedEvent, InventoryEvent
from modules.inventory.ports import AuditLogger, AudienceServicePort
from utils.audit import clean_sensitive


@dataclass(slots=True, frozen=True)
class CreateAudienceResult:
    audience: AudienceShortResponse
    events: list[InventoryEvent]


@dataclass(slots=True, frozen=True)
class UpdateAudienceResult:
    audience: AudienceShortResponse
    events: list[InventoryEvent]


@dataclass(slots=True, frozen=True)
class DeleteAudienceResult:
    events: list[InventoryEvent]


class InventoryAudienceUseCases:
    def __init__(self, audience_service: AudienceServicePort) -> None:
        self.audience_service = audience_service

    async def list_audiences(self) -> list[AudienceResponse]:
        audiences = await self.audience_service.get_list()
        return list(audiences)

    async def get_audience(self, *, audience_public_id: UUID) -> AudienceResponse:
        return await self.audience_service.get_one_by_public_id(audience_public_id)

    async def create_audience(
        self,
        *,
        data: AudienceCreate,
        audit: AuditLogger,
    ) -> CreateAudienceResult:
        created = await self.audience_service.create_audience(data)

        await audit.log(
            action="audience.create",
            entity_type="audience",
            entity_id=created.id,
            payload=self._audit_payload(data),
        )

        return CreateAudienceResult(
            audience=created,
            events=[AudienceUpdatedEvent(created.id)],
        )

    async def update_audience(
        self,
        *,
        audience_public_id: UUID,
        data: AudienceUpdate,
        audit: AuditLogger,
    ) -> UpdateAudienceResult:
        updated = await self.audience_service.update_audience_by_public_id(audience_public_id, data)

        await audit.log(
            action="audience.update",
            entity_type="audience",
            entity_id=updated.id,
            payload=self._audit_payload(data),
        )

        return UpdateAudienceResult(
            audience=updated,
            events=[AudienceUpdatedEvent(updated.id)],
        )

    async def delete_audience(
        self,
        *,
        audience_public_id: UUID,
        audit: AuditLogger,
    ) -> DeleteAudienceResult:
        audience = await self.audience_service.get_one_by_public_id(audience_public_id)
        await self.audience_service.delete_audience(audience.id)

        await audit.log(
            action="audience.delete",
            entity_type="audience",
            entity_id=audience.id,
            payload=None,
        )

        return DeleteAudienceResult(events=[AudienceUpdatedEvent(audience.id)])

    @staticmethod
    def _audit_payload(data: AudienceCreate | AudienceUpdate) -> dict | None:
        payload = clean_sensitive(data)
        if isinstance(payload, dict) and "hardware" in payload:
            payload["hardware_count"] = len(payload.get("hardware") or [])
            payload.pop("hardware", None)
        return payload
