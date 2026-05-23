from dataclasses import dataclass

from core.exceptions import OfficeNotFoundError
from models import Office
from schemas.office import OfficeCreate, OfficeResponse, OfficeShort, OfficeUpdate
from modules.inventory.ports import AuditLogger, OfficeServicePort
from utils.audit import changed_fields


@dataclass(slots=True, frozen=True)
class CreateOfficeResult:
    office: Office


@dataclass(slots=True, frozen=True)
class UpdateOfficeResult:
    office: Office


@dataclass(slots=True, frozen=True)
class DeleteOfficeResult:
    pass


class InventoryOfficeUseCases:
    def __init__(self, office_service: OfficeServicePort) -> None:
        self.office_service = office_service

    async def list_offices(self) -> list[OfficeResponse | OfficeShort]:
        offices = await self.office_service.get_all()
        return list(offices)

    async def list_offices_short(self) -> list[OfficeShort]:
        offices = await self.office_service.get_all_short()
        return list(offices)

    async def get_office(self, *, office_id: int) -> OfficeResponse:
        office = await self.office_service.get(office_id)
        if not office:
            raise OfficeNotFoundError()
        return office

    async def create_office(
        self,
        *,
        data: OfficeCreate,
        audit: AuditLogger,
    ) -> CreateOfficeResult:
        office = await self.office_service.create(data)

        await audit.log(
            action="office.create",
            entity_type="office",
            entity_id=office.id,
            payload={"address": office.address},
        )

        return CreateOfficeResult(office=office)

    async def update_office(
        self,
        *,
        office_id: int,
        data: OfficeUpdate,
        audit: AuditLogger,
    ) -> UpdateOfficeResult:
        updated_office = await self.office_service.update(office_id, data)
        if not updated_office:
            raise OfficeNotFoundError()

        await audit.log(
            action="office.update",
            entity_type="office",
            entity_id=office_id,
            payload={
                "office_id": office_id,
                "changed_fields": changed_fields(data),
            },
        )

        return UpdateOfficeResult(office=updated_office)

    async def delete_office(
        self,
        *,
        office_id: int,
        audit: AuditLogger,
    ) -> DeleteOfficeResult:
        deleted = await self.office_service.delete(office_id)
        if not deleted:
            raise OfficeNotFoundError()

        await audit.log(
            action="office.delete",
            entity_type="office",
            entity_id=office_id,
        )

        return DeleteOfficeResult()
