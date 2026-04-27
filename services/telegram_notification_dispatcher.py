from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from loguru import logger

from core.exceptions import TelegramNotificationAudienceNotFoundError
from schemas.telegram import TelegramEventType
from services.telegram_delivery_service import (
    TelegramBroadcastDeliveryResult,
    TelegramDeliveryResult,
)
from services.telegram_notification_renderer import TelegramNotificationRenderer


class TelegramRecipientProviderPort(Protocol):
    async def get_hardware_event_recipient_ids(
        self,
        *,
        audience_id: int,
        event_type: TelegramEventType,
        exclude_user_id: int | None = None,
    ) -> list[int]: ...

    async def get_user_event_recipient_ids(
        self,
        *,
        user_id: int,
        event_type: TelegramEventType,
    ) -> list[int]: ...


class TelegramDeliveryPort(Protocol):
    async def deliver_to_recipients(
        self,
        *,
        recipient_ids: list[int],
        message: str,
        notification_id: str,
        event_type: str,
    ) -> TelegramBroadcastDeliveryResult: ...


class TelegramDeliveryLogPort(Protocol):
    async def save_results(
        self,
        *,
        notification_id: str,
        event_type: str,
        payload: dict,
        results: Sequence[TelegramDeliveryResult],
    ) -> None: ...


@dataclass(slots=True, frozen=True)
class HardwareStateNotification:
    hardware_id: int
    audience_id: int
    event_type: str
    hardware_type: str | None = None
    title: str | None = None
    description: str | None = None
    inv_number: str | None = None
    x: int | None = None
    y: int | None = None
    actor_user_id: int | None = None

    def delivery_payload(self) -> dict:
        return {
            "hardware_id": self.hardware_id,
            "audience_id": self.audience_id,
            "hardware_type": self.hardware_type,
            "title": self.title,
            "description": self.description,
            "inv_number": self.inv_number,
            "x": self.x,
            "y": self.y,
            "actor_user_id": self.actor_user_id,
        }


@dataclass(slots=True, frozen=True)
class AuthSecurityNotification:
    user_id: int
    event_name: str
    ip: str | None = None
    user_agent: str | None = None

    @property
    def event_type(self) -> str:
        return TelegramEventType.auth_security.value

    def delivery_payload(self) -> dict:
        return {
            "user_id": self.user_id,
            "event_name": self.event_name,
            "ip": self.ip,
            "user_agent": self.user_agent,
        }


@dataclass(slots=True, frozen=True)
class TelegramNotificationDispatchResult:
    sent: int
    failed: int
    event_type: str

    def as_task_result(self) -> dict[str, int | str]:
        return {
            "sent": self.sent,
            "failed": self.failed,
            "event_type": self.event_type,
        }


class TelegramNotificationDispatcher:
    def __init__(
        self,
        *,
        recipients: TelegramRecipientProviderPort,
        renderer: TelegramNotificationRenderer,
        delivery: TelegramDeliveryPort,
        delivery_logs: TelegramDeliveryLogPort,
        enabled: bool,
        bot_token_configured: bool,
        notification_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.recipients = recipients
        self.renderer = renderer
        self.delivery = delivery
        self.delivery_logs = delivery_logs
        self.enabled = enabled
        self.bot_token_configured = bot_token_configured
        self.notification_id_factory = notification_id_factory or (lambda: uuid4().hex)

    async def send_hardware_state(
        self,
        notification: HardwareStateNotification,
    ) -> TelegramNotificationDispatchResult:
        event_type = notification.event_type
        if skip_result := self._skip_if_disabled(event_type):
            logger.info(
                "Telegram notification skipped: telegram disabled event_type={} hardware_id={}",
                event_type,
                notification.hardware_id,
            )
            return skip_result

        if skip_result := self._skip_if_bot_token_missing(event_type):
            logger.warning(
                "Telegram notification skipped: bot token is not configured event_type={} hardware_id={}",
                event_type,
                notification.hardware_id,
            )
            return skip_result

        try:
            telegram_event_type = TelegramEventType(event_type)
        except ValueError:
            logger.warning(
                "Telegram notification skipped: unsupported event type {} for hardware_id={}",
                event_type,
                notification.hardware_id,
            )
            return self._empty_result(event_type)

        try:
            recipient_ids = await self.recipients.get_hardware_event_recipient_ids(
                audience_id=notification.audience_id,
                event_type=telegram_event_type,
                exclude_user_id=notification.actor_user_id,
            )
        except TelegramNotificationAudienceNotFoundError:
            logger.warning(
                "Telegram notification skipped: audience not found audience_id={} hardware_id={}",
                notification.audience_id,
                notification.hardware_id,
            )
            return self._empty_result(event_type)

        if not recipient_ids:
            logger.info(
                "Telegram notification skipped: no subscribers audience_id={} event_type={} hardware_id={}",
                notification.audience_id,
                event_type,
                notification.hardware_id,
            )
            return self._empty_result(event_type)

        message = self.renderer.build_hardware_state_message(
            hardware_id=notification.hardware_id,
            audience_id=notification.audience_id,
            event_type=telegram_event_type,
            hardware_type=notification.hardware_type,
            title=notification.title,
            description=notification.description,
            inv_number=notification.inv_number,
            x=notification.x,
            y=notification.y,
        )
        notification_id = self.notification_id_factory()
        logger.info(
            "Telegram hardware notification started: notification_id={} event_type={} hardware_id={} audience_id={}",
            notification_id,
            event_type,
            notification.hardware_id,
            notification.audience_id,
        )
        delivery_result = await self.delivery.deliver_to_recipients(
            recipient_ids=recipient_ids,
            message=message,
            notification_id=notification_id,
            event_type=event_type,
        )
        await self._save_delivery_logs(
            notification_id=notification_id,
            event_type=event_type,
            payload=notification.delivery_payload(),
            results=delivery_result.results,
            log_context=(
                "Telegram delivery log persistence failed: notification_id={} "
                "event_type={} hardware_id={} audience_id={}"
            ),
            log_args=(
                notification_id,
                event_type,
                notification.hardware_id,
                notification.audience_id,
            ),
        )

        logger.info(
            "Telegram notification processed: notification_id={} event_type={} hardware_id={} audience_id={} recipients={} sent={} failed={}",
            notification_id,
            event_type,
            notification.hardware_id,
            notification.audience_id,
            len(recipient_ids),
            delivery_result.sent,
            delivery_result.failed,
        )
        return TelegramNotificationDispatchResult(
            sent=delivery_result.sent,
            failed=delivery_result.failed,
            event_type=event_type,
        )

    async def send_auth_security(
        self,
        notification: AuthSecurityNotification,
    ) -> TelegramNotificationDispatchResult:
        event_type = notification.event_type
        if skip_result := self._skip_if_disabled(event_type):
            logger.info(
                "Telegram auth security notification skipped: telegram disabled user_id={} event_name={}",
                notification.user_id,
                notification.event_name,
            )
            return skip_result

        if skip_result := self._skip_if_bot_token_missing(event_type):
            logger.warning(
                "Telegram auth security notification skipped: bot token is not configured user_id={} event_name={}",
                notification.user_id,
                notification.event_name,
            )
            return skip_result

        recipient_ids = await self.recipients.get_user_event_recipient_ids(
            user_id=notification.user_id,
            event_type=TelegramEventType.auth_security,
        )
        if not recipient_ids:
            logger.info(
                "Telegram auth security notification skipped: no subscribers user_id={} event_name={}",
                notification.user_id,
                notification.event_name,
            )
            return self._empty_result(event_type)

        message = self.renderer.build_auth_security_message(
            event_name=notification.event_name,
            ip=notification.ip,
            user_agent=notification.user_agent,
        )
        notification_id = self.notification_id_factory()
        logger.info(
            "Telegram auth security notification started: notification_id={} user_id={} event_name={}",
            notification_id,
            notification.user_id,
            notification.event_name,
        )
        delivery_result = await self.delivery.deliver_to_recipients(
            recipient_ids=recipient_ids,
            message=message,
            notification_id=notification_id,
            event_type=event_type,
        )
        await self._save_delivery_logs(
            notification_id=notification_id,
            event_type=event_type,
            payload=notification.delivery_payload(),
            results=delivery_result.results,
            log_context=(
                "Telegram delivery log persistence failed: notification_id={} "
                "event_type={} user_id={} event_name={}"
            ),
            log_args=(
                notification_id,
                event_type,
                notification.user_id,
                notification.event_name,
            ),
        )

        logger.info(
            "Telegram auth security notification processed: notification_id={} user_id={} event_name={} recipients={} sent={} failed={}",
            notification_id,
            notification.user_id,
            notification.event_name,
            len(recipient_ids),
            delivery_result.sent,
            delivery_result.failed,
        )
        return TelegramNotificationDispatchResult(
            sent=delivery_result.sent,
            failed=delivery_result.failed,
            event_type=event_type,
        )

    async def _save_delivery_logs(
        self,
        *,
        notification_id: str,
        event_type: str,
        payload: dict,
        results: Sequence[TelegramDeliveryResult],
        log_context: str,
        log_args: tuple,
    ) -> None:
        try:
            await self.delivery_logs.save_results(
                notification_id=notification_id,
                event_type=event_type,
                payload=payload,
                results=results,
            )
        except Exception:
            logger.exception(log_context, *log_args)

    def _skip_if_disabled(self, event_type: str) -> TelegramNotificationDispatchResult | None:
        if self.enabled:
            return None
        return self._empty_result(event_type)

    def _skip_if_bot_token_missing(self, event_type: str) -> TelegramNotificationDispatchResult | None:
        if self.bot_token_configured:
            return None
        return self._empty_result(event_type)

    @staticmethod
    def _empty_result(event_type: str) -> TelegramNotificationDispatchResult:
        return TelegramNotificationDispatchResult(sent=0, failed=0, event_type=event_type)
