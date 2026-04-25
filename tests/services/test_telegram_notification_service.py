import asyncio
from types import SimpleNamespace

from schemas.telegram import TelegramEventType
from services.telegram_notification_service import TelegramNotificationService


class FakeTelegramSubscriptionRepo:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def list_recipient_telegram_ids(
        self,
        *,
        event_type: str,
        scopes: list[tuple[str, int]],
        exclude_user_id: int | None = None,
    ) -> list[int]:
        self.calls.append(
            {
                "event_type": event_type,
                "scopes": scopes,
                "exclude_user_id": exclude_user_id,
            }
        )
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
            exclude_user_id=7,
        )

        assert result == [101, 202]
        assert repo.calls == [
            {
                "event_type": TelegramEventType.hardware_fault.value,
                "scopes": [("audience", 15), ("office", 7)],
                "exclude_user_id": 7,
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
        hardware_type="computer",
        title="Рабочая станция",
        description="Не включается после подачи питания",
        inv_number="INV-55",
        x=6,
        y=2,
    )

    assert "🚨 <b>Неисправность оборудования</b>" in message
    assert "Аудитория: <code>215</code>" in message
    assert "Оборудование: <code>42</code>" in message
    assert "Тип: компьютер" in message
    assert "Место: ряд 3, позиция 7" in message
    assert "Название: Рабочая станция" in message
    assert "Комментарий: Не включается после подачи питания" in message
    assert "Инвентарный номер: <code>INV-55</code>" in message


def test_build_hardware_state_message_escapes_dynamic_fields() -> None:
    service = TelegramNotificationService(
        FakeTelegramSubscriptionRepo(),
        FakeAudienceRepo(),
    )

    message = service.build_hardware_state_message(
        hardware_id=42,
        audience_id=215,
        event_type=TelegramEventType.hardware_fault,
        title="<monitor>",
        description="broken <again>",
    )

    assert "&lt;monitor&gt;" in message
    assert "broken &lt;again&gt;" in message
