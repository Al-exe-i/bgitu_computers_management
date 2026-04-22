import asyncio
from types import SimpleNamespace

from schemas.telegram import TelegramEventType
from services.telegram_notification_service import TelegramNotificationService


class FakeTelegramSubscriptionRepo:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def list_recipient_telegram_ids(self, *, event_type: str, scopes: list[tuple[str, int]]) -> list[int]:
        self.calls.append({"event_type": event_type, "scopes": scopes})
        return [101, 202]


class FakeAudienceRepo:
    async def get_by_id(self, audience_id: int):
        return SimpleNamespace(id=audience_id, office_id=7)


def test_get_hardware_event_recipient_ids_uses_audience_and_office_scopes() -> None:
    async def scenario() -> None:
        repo = FakeTelegramSubscriptionRepo()
        service = TelegramNotificationService(repo, FakeAudienceRepo())

        result = await service.get_hardware_event_recipient_ids(
            audience_id=15,
            event_type=TelegramEventType.hardware_fault,
        )

        assert result == [101, 202]
        assert repo.calls == [
            {
                "event_type": TelegramEventType.hardware_fault.value,
                "scopes": [("audience", 15), ("office", 7)],
            }
        ]

    asyncio.run(scenario())


def test_build_hardware_state_message_formats_fault_event() -> None:
    service = TelegramNotificationService(
        FakeTelegramSubscriptionRepo(),
        FakeAudienceRepo(),
    )

    message = service.build_hardware_state_message(
        hardware_id=42,
        audience_id=215,
        event_type=TelegramEventType.hardware_fault,
        title="Рабочая станция",
        inv_number="INV-55",
        x=6,
        y=2,
    )

    assert "🚨" in message
    assert "🏫 Аудитория: 215" in message
    assert "🖥 ID оборудования: 42" in message
    assert "📍 Расположение: ряд 3, место 7" in message
    assert "🏷 Название: Рабочая станция" in message
    assert "🔢 Инвентарный номер: INV-55" in message
