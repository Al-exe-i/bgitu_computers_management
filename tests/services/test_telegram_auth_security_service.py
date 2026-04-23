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


def test_get_user_event_recipient_ids_uses_user_scope() -> None:
    async def scenario() -> None:
        repo = FakeTelegramSubscriptionRepo()
        service = TelegramNotificationService(repo, FakeAudienceRepo())

        result = await service.get_user_event_recipient_ids(
            user_id=7,
            event_type=TelegramEventType.auth_security,
        )

        assert result == [101, 202]
        assert repo.calls == [
            {
                "event_type": TelegramEventType.auth_security.value,
                "scopes": [("user", 7)],
            }
        ]

    asyncio.run(scenario())


def test_build_auth_security_message_formats_login_event() -> None:
    service = TelegramNotificationService(
        FakeTelegramSubscriptionRepo(),
        FakeAudienceRepo(),
    )

    message = service.build_auth_security_message(
        event_name="Выполнен вход в аккаунт",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    assert "🔐 Выполнен вход в аккаунт" in message
    assert "В аккаунт выполнен новый вход." in message
    assert "🌐 IP: 127.0.0.1" in message
    assert "💻 Устройство: pytest" in message


def test_build_auth_security_message_formats_password_change_event() -> None:
    service = TelegramNotificationService(
        FakeTelegramSubscriptionRepo(),
        FakeAudienceRepo(),
    )

    message = service.build_auth_security_message(
        event_name="Изменён пароль аккаунта",
    )

    assert "🔑 Изменён пароль аккаунта" in message
    assert "Пароль вашего аккаунта был изменён." in message
