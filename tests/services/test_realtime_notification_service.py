import asyncio
from types import SimpleNamespace

from schemas.notification import NotificationEventType, NotificationScopeType
from services.realtime_notification_service import (
    AuthSecurityNotification,
    HardwareStateNotification,
    RealtimeNotificationDispatcher,
    RealtimeNotificationRecipientService,
    RealtimeNotificationRenderer,
)


class FakeSubscriptionRepo:
    def __init__(self, recipients: list[int]) -> None:
        self.recipients = recipients
        self.calls: list[dict] = []

    async def list_recipient_user_ids(
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
        return [user_id for user_id in self.recipients if user_id != exclude_user_id]


class FakeAudienceRepo:
    async def get_one_short(self, audience_id: int):
        return SimpleNamespace(id=audience_id, office_id=5)


class FakePublisher:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def publish_notification(self, *, user_id: int, payload: dict) -> None:
        self.messages.append({"user_id": user_id, "payload": payload})


def test_recipient_service_uses_audience_and_office_scopes_and_excludes_actor() -> None:
    async def scenario() -> None:
        subscription_repo = FakeSubscriptionRepo([1, 2, 3])
        service = RealtimeNotificationRecipientService(
            subscription_repo,
            FakeAudienceRepo(),
        )

        recipients = await service.get_hardware_event_recipient_user_ids(
            audience_id=10,
            event_type=NotificationEventType.hardware_fault,
            exclude_user_id=2,
        )

        assert recipients == [1, 3]
        assert subscription_repo.calls == [
            {
                "event_type": NotificationEventType.hardware_fault.value,
                "scopes": [
                    (NotificationScopeType.audience.value, 10),
                    (NotificationScopeType.office.value, 5),
                ],
                "exclude_user_id": 2,
            }
        ]

    asyncio.run(scenario())


def test_dispatcher_sends_hardware_fault_payload_to_recipients() -> None:
    async def scenario() -> None:
        publisher = FakePublisher()
        dispatcher = RealtimeNotificationDispatcher(
            recipients=RealtimeNotificationRecipientService(
                FakeSubscriptionRepo([8, 9]),
                FakeAudienceRepo(),
            ),
            renderer=RealtimeNotificationRenderer(),
            publisher=publisher,
        )

        result = await dispatcher.send_hardware_state(
            HardwareStateNotification(
                previous_state=True,
                state=False,
                hardware_id=44,
                audience_id=10,
                hardware_type="server",
                title=None,
                x=1,
                y=2,
                actor_user_id=8,
            )
        )

        assert result.sent == 1
        assert result.event_type == NotificationEventType.hardware_fault.value
        assert publisher.messages[0]["user_id"] == 9
        payload = publisher.messages[0]["payload"]
        assert payload["event_type"] == NotificationEventType.hardware_fault.value
        assert payload["title"] == "Оборудование неисправно"
        assert payload["entity_type"] == "hardware"
        assert payload["payload"]["hardware_id"] == 44

    asyncio.run(scenario())


def test_dispatcher_skips_unchanged_hardware_state() -> None:
    async def scenario() -> None:
        publisher = FakePublisher()
        dispatcher = RealtimeNotificationDispatcher(
            recipients=RealtimeNotificationRecipientService(
                FakeSubscriptionRepo([8]),
                FakeAudienceRepo(),
            ),
            renderer=RealtimeNotificationRenderer(),
            publisher=publisher,
        )

        result = await dispatcher.send_hardware_state(
            HardwareStateNotification(
                previous_state=True,
                state=True,
                hardware_id=44,
                audience_id=10,
            )
        )

        assert result.sent == 0
        assert publisher.messages == []

    asyncio.run(scenario())


def test_dispatcher_sends_auth_security_payload_to_user_scope() -> None:
    async def scenario() -> None:
        publisher = FakePublisher()
        dispatcher = RealtimeNotificationDispatcher(
            recipients=RealtimeNotificationRecipientService(
                FakeSubscriptionRepo([7]),
                FakeAudienceRepo(),
            ),
            renderer=RealtimeNotificationRenderer(),
            publisher=publisher,
        )

        result = await dispatcher.send_auth_security(
            AuthSecurityNotification(
                user_id=7,
                event_name="Новый вход",
                ip="127.0.0.1",
                user_agent="pytest",
            )
        )

        assert result.sent == 1
        assert publisher.messages[0]["payload"]["event_type"] == NotificationEventType.auth_security.value
        assert publisher.messages[0]["payload"]["title"] == "Событие безопасности"

    asyncio.run(scenario())
