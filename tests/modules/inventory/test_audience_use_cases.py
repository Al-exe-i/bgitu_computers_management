import asyncio
from types import SimpleNamespace

from modules.inventory.application import InventoryAudienceUseCases
from modules.inventory.events import AudienceUpdatedEvent
from schemas.audience import AudienceCreate, AudienceUpdate


class FakeAudienceService:
    def __init__(self) -> None:
        self.created: list[AudienceCreate] = []
        self.updated: list[tuple[int, AudienceUpdate]] = []
        self.deleted: list[int] = []

    async def create_audience(self, data: AudienceCreate):
        self.created.append(data)
        return SimpleNamespace(id=12, number=data.number)

    async def update_audience(self, audience_id: int, data: AudienceUpdate):
        self.updated.append((audience_id, data))
        return SimpleNamespace(id=audience_id)

    async def delete_audience(self, audience_id: int) -> None:
        self.deleted.append(audience_id)


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs):
        self.logs.append(kwargs)


def test_create_audience_logs_compact_payload_and_returns_event() -> None:
    async def scenario() -> None:
        service = FakeAudienceService()
        audit = FakeAudit()
        use_cases = InventoryAudienceUseCases(service)

        result = await use_cases.create_audience(
            data=AudienceCreate(
                number=212,
                floor=2,
                description="212",
                office_id=1,
                width=10,
                height=10,
                hardware=[],
            ),
            audit=audit,
        )

        assert result.audience.id == 12
        assert result.events == [AudienceUpdatedEvent(audience_id=12)]
        assert audit.logs[0]["action"] == "audience.create"
        assert audit.logs[0]["payload"]["hardware_count"] == 0
        assert "hardware" not in audit.logs[0]["payload"]

    asyncio.run(scenario())


def test_delete_audience_logs_and_returns_event() -> None:
    async def scenario() -> None:
        service = FakeAudienceService()
        audit = FakeAudit()
        use_cases = InventoryAudienceUseCases(service)

        result = await use_cases.delete_audience(audience_id=12, audit=audit)

        assert service.deleted == [12]
        assert result.events == [AudienceUpdatedEvent(audience_id=12)]
        assert audit.logs == [
            {
                "action": "audience.delete",
                "entity_type": "audience",
                "entity_id": 12,
                "payload": None,
            }
        ]

    asyncio.run(scenario())
