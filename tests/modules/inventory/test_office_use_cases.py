import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import OfficeNotFoundError
from modules.inventory.application import InventoryOfficeUseCases
from schemas.office import OfficeCreate, OfficeUpdate


class FakeOfficeService:
    def __init__(self, office=None, *, delete_result: bool = True) -> None:
        self.office = office
        self.delete_result = delete_result
        self.created: list[OfficeCreate] = []
        self.updated: list[tuple[int, OfficeUpdate]] = []
        self.deleted: list[int] = []

    async def get(self, office_id: int):
        if self.office and self.office.id == office_id:
            return self.office
        return None

    async def create(self, data: OfficeCreate):
        self.created.append(data)
        return SimpleNamespace(id=data.id, address=data.address)

    async def update(self, office_id: int, data: OfficeUpdate):
        self.updated.append((office_id, data))
        if self.office is None:
            return None

        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(self.office, key, value)
        return self.office

    async def delete(self, office_id: int) -> bool:
        self.deleted.append(office_id)
        return self.delete_result


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs):
        self.logs.append(kwargs)


def test_create_office_writes_audit_payload() -> None:
    async def scenario() -> None:
        service = FakeOfficeService()
        audit = FakeAudit()
        use_cases = InventoryOfficeUseCases(service)

        result = await use_cases.create_office(
            data=OfficeCreate(id=1, address="Main building"),
            audit=audit,
        )

        assert result.office.id == 1
        assert service.created == [OfficeCreate(id=1, address="Main building")]
        assert audit.logs == [
            {
                "action": "office.create",
                "entity_type": "office",
                "entity_id": 1,
                "payload": {"address": "Main building"},
            }
        ]

    asyncio.run(scenario())


def test_update_office_writes_changed_fields() -> None:
    async def scenario() -> None:
        office = SimpleNamespace(id=1, address="Old address")
        service = FakeOfficeService(office)
        audit = FakeAudit()
        use_cases = InventoryOfficeUseCases(service)

        result = await use_cases.update_office(
            office_id=1,
            data=OfficeUpdate(address="New address"),
            audit=audit,
        )

        assert result.office.address == "New address"
        assert audit.logs == [
            {
                "action": "office.update",
                "entity_type": "office",
                "entity_id": 1,
                "payload": {
                    "office_id": 1,
                    "changed_fields": ["address"],
                },
            }
        ]

    asyncio.run(scenario())


def test_delete_office_not_found_does_not_write_audit() -> None:
    async def scenario() -> None:
        service = FakeOfficeService(delete_result=False)
        audit = FakeAudit()
        use_cases = InventoryOfficeUseCases(service)

        with pytest.raises(OfficeNotFoundError):
            await use_cases.delete_office(office_id=404, audit=audit)

        assert service.deleted == [404]
        assert audit.logs == []

    asyncio.run(scenario())


def test_get_office_not_found_raises_application_error() -> None:
    async def scenario() -> None:
        use_cases = InventoryOfficeUseCases(FakeOfficeService())

        with pytest.raises(OfficeNotFoundError):
            await use_cases.get_office(office_id=404)

    asyncio.run(scenario())
