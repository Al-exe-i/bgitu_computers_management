import asyncio

from core.exceptions import TelegramNotificationAudienceNotFoundError
from schemas.telegram import TelegramEventType
from services.telegram_delivery_service import (
    TelegramBroadcastDeliveryResult,
    TelegramDeliveryResult,
)
from services.telegram_notification_dispatcher import (
    AuthSecurityNotification,
    HardwareStateNotification,
    TelegramNotificationDispatcher,
)


class FakeRecipients:
    def __init__(
        self,
        *,
        hardware_recipients: list[int] | None = None,
        user_recipients: list[int] | None = None,
        missing_audience: bool = False,
    ) -> None:
        self.hardware_recipients = hardware_recipients or []
        self.user_recipients = user_recipients or []
        self.missing_audience = missing_audience
        self.hardware_calls: list[dict] = []
        self.user_calls: list[dict] = []

    async def get_hardware_event_recipient_ids(
        self,
        *,
        audience_id: int,
        event_type: TelegramEventType,
        exclude_user_id: int | None = None,
    ) -> list[int]:
        self.hardware_calls.append(
            {
                "audience_id": audience_id,
                "event_type": event_type,
                "exclude_user_id": exclude_user_id,
            }
        )
        if self.missing_audience:
            raise TelegramNotificationAudienceNotFoundError()
        return self.hardware_recipients

    async def get_user_event_recipient_ids(
        self,
        *,
        user_id: int,
        event_type: TelegramEventType,
    ) -> list[int]:
        self.user_calls.append({"user_id": user_id, "event_type": event_type})
        return self.user_recipients


class FakeRenderer:
    def __init__(self) -> None:
        self.hardware_calls: list[dict] = []
        self.auth_calls: list[dict] = []

    def build_hardware_state_message(self, **kwargs) -> str:
        self.hardware_calls.append(kwargs)
        return "hardware-message"

    def build_auth_security_message(self, **kwargs) -> str:
        self.auth_calls.append(kwargs)
        return "auth-message"


class FakeDelivery:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.result = TelegramBroadcastDeliveryResult(
            sent=1,
            failed=1,
            results=[
                TelegramDeliveryResult(telegram_id=101, delivered=True, attempts=1),
                TelegramDeliveryResult(
                    telegram_id=202,
                    delivered=False,
                    attempts=1,
                    error_type="TelegramForbiddenError",
                ),
            ],
        )

    async def deliver_to_recipients(self, **kwargs) -> TelegramBroadcastDeliveryResult:
        self.calls.append(kwargs)
        return self.result


class FakeDeliveryLogs:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def save_results(self, **kwargs) -> None:
        self.calls.append(kwargs)


def make_dispatcher(
    *,
    recipients: FakeRecipients,
    renderer: FakeRenderer | None = None,
    delivery: FakeDelivery | None = None,
    delivery_logs: FakeDeliveryLogs | None = None,
    enabled: bool = True,
    bot_token_configured: bool = True,
) -> TelegramNotificationDispatcher:
    return TelegramNotificationDispatcher(
        recipients=recipients,
        renderer=renderer or FakeRenderer(),
        delivery=delivery or FakeDelivery(),
        delivery_logs=delivery_logs or FakeDeliveryLogs(),
        enabled=enabled,
        bot_token_configured=bot_token_configured,
        notification_id_factory=lambda: "notif-1",
    )


def test_dispatch_hardware_state_delivers_and_logs() -> None:
    async def scenario() -> None:
        recipients = FakeRecipients(hardware_recipients=[101, 202])
        renderer = FakeRenderer()
        delivery = FakeDelivery()
        delivery_logs = FakeDeliveryLogs()
        dispatcher = make_dispatcher(
            recipients=recipients,
            renderer=renderer,
            delivery=delivery,
            delivery_logs=delivery_logs,
        )

        result = await dispatcher.send_hardware_state(
            HardwareStateNotification(
                hardware_id=42,
                audience_id=215,
                event_type=TelegramEventType.hardware_fault.value,
                hardware_type="computer",
                title="PC-1",
                actor_user_id=7,
            )
        )

        assert result.as_task_result() == {
            "sent": 1,
            "failed": 1,
            "event_type": TelegramEventType.hardware_fault.value,
        }
        assert recipients.hardware_calls == [
            {
                "audience_id": 215,
                "event_type": TelegramEventType.hardware_fault,
                "exclude_user_id": 7,
            }
        ]
        assert renderer.hardware_calls[0]["hardware_id"] == 42
        assert delivery.calls[0]["recipient_ids"] == [101, 202]
        assert delivery.calls[0]["message"] == "hardware-message"
        assert delivery.calls[0]["notification_id"] == "notif-1"
        assert delivery_logs.calls[0]["payload"]["hardware_id"] == 42
        assert delivery_logs.calls[0]["payload"]["actor_user_id"] == 7
        assert delivery_logs.calls[0]["results"] == delivery.result.results

    asyncio.run(scenario())


def test_dispatch_hardware_state_skips_when_audience_is_missing() -> None:
    async def scenario() -> None:
        delivery = FakeDelivery()
        delivery_logs = FakeDeliveryLogs()
        dispatcher = make_dispatcher(
            recipients=FakeRecipients(missing_audience=True),
            delivery=delivery,
            delivery_logs=delivery_logs,
        )

        result = await dispatcher.send_hardware_state(
            HardwareStateNotification(
                hardware_id=42,
                audience_id=215,
                event_type=TelegramEventType.hardware_fault.value,
            )
        )

        assert result.as_task_result() == {
            "sent": 0,
            "failed": 0,
            "event_type": TelegramEventType.hardware_fault.value,
        }
        assert delivery.calls == []
        assert delivery_logs.calls == []

    asyncio.run(scenario())


def test_dispatch_auth_security_delivers_and_logs() -> None:
    async def scenario() -> None:
        recipients = FakeRecipients(user_recipients=[303])
        renderer = FakeRenderer()
        delivery = FakeDelivery()
        delivery_logs = FakeDeliveryLogs()
        dispatcher = make_dispatcher(
            recipients=recipients,
            renderer=renderer,
            delivery=delivery,
            delivery_logs=delivery_logs,
        )

        result = await dispatcher.send_auth_security(
            AuthSecurityNotification(
                user_id=7,
                event_name="login",
                ip="127.0.0.1",
                user_agent="pytest",
            )
        )

        assert result.as_task_result() == {
            "sent": 1,
            "failed": 1,
            "event_type": TelegramEventType.auth_security.value,
        }
        assert recipients.user_calls == [
            {"user_id": 7, "event_type": TelegramEventType.auth_security}
        ]
        assert renderer.auth_calls == [
            {
                "event_name": "login",
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            }
        ]
        assert delivery.calls[0]["recipient_ids"] == [303]
        assert delivery.calls[0]["message"] == "auth-message"
        assert delivery_logs.calls[0]["payload"] == {
            "user_id": 7,
            "event_name": "login",
            "ip": "127.0.0.1",
            "user_agent": "pytest",
        }

    asyncio.run(scenario())


def test_dispatch_skips_before_recipient_lookup_when_disabled() -> None:
    async def scenario() -> None:
        recipients = FakeRecipients(hardware_recipients=[101])
        delivery = FakeDelivery()
        dispatcher = make_dispatcher(
            recipients=recipients,
            delivery=delivery,
            enabled=False,
        )

        result = await dispatcher.send_hardware_state(
            HardwareStateNotification(
                hardware_id=42,
                audience_id=215,
                event_type=TelegramEventType.hardware_fault.value,
            )
        )

        assert result.as_task_result() == {
            "sent": 0,
            "failed": 0,
            "event_type": TelegramEventType.hardware_fault.value,
        }
        assert recipients.hardware_calls == []
        assert delivery.calls == []

    asyncio.run(scenario())
