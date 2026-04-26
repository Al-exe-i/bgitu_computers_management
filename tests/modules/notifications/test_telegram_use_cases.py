import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from modules.notifications.application import TelegramIntegrationUseCases
from schemas.telegram import (
    TelegramDeliveryMode,
    TelegramEventType,
    TelegramLinkStartResponse,
    TelegramLinkStatusResponse,
    TelegramScopeType,
    TelegramSubscriptionCreate,
    TelegramSubscriptionResponse,
)


EXPIRES_AT = datetime(2026, 4, 28, tzinfo=timezone.utc)
CREATED_AT = datetime(2026, 4, 21, tzinfo=timezone.utc)


class FakeTelegramLinkService:
    def __init__(self) -> None:
        self.link_tokens: list[int] = []
        self.unlinked_users: list[int] = []

    async def get_link_status(self, user_id: int) -> TelegramLinkStatusResponse:
        return TelegramLinkStatusResponse(
            telegram_id="1001",
            telegram_id_confirmed=True,
        )

    async def create_link_token(self, user_id: int) -> TelegramLinkStartResponse:
        self.link_tokens.append(user_id)
        return TelegramLinkStartResponse(
            link_token="raw-token",
            expires_at=EXPIRES_AT,
            bot_username="bgitu_test_bot",
            bot_deep_link="https://t.me/bgitu_test_bot?start=link_raw-token",
        )

    async def unlink_user(self, user_id: int) -> TelegramLinkStatusResponse:
        self.unlinked_users.append(user_id)
        return TelegramLinkStatusResponse(
            telegram_id=None,
            telegram_id_confirmed=False,
        )


class FakeTelegramSubscriptionService:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.deleted: list[dict] = []

    async def list_for_user(self, user_id: int) -> list[TelegramSubscriptionResponse]:
        return []

    async def create(
        self,
        *,
        user_id: int,
        data: TelegramSubscriptionCreate,
    ) -> TelegramSubscriptionResponse:
        self.created.append({"user_id": user_id, "data": data})
        return TelegramSubscriptionResponse(
            id=5,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
            event_type=data.event_type,
            delivery_mode=data.delivery_mode,
            enabled=True,
            created_at=CREATED_AT,
        )

    async def delete(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> None:
        self.deleted.append({"user_id": user_id, "subscription_id": subscription_id})


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


@dataclass(slots=True)
class Actor:
    id: int
    telegram_id: int | None


def make_use_cases(
    *,
    link_service: FakeTelegramLinkService | None = None,
    subscription_service: FakeTelegramSubscriptionService | None = None,
) -> TelegramIntegrationUseCases:
    return TelegramIntegrationUseCases(
        link_service=link_service or FakeTelegramLinkService(),
        subscription_service=subscription_service or FakeTelegramSubscriptionService(),
    )


def test_create_link_token_writes_audit() -> None:
    async def scenario() -> None:
        link_service = FakeTelegramLinkService()
        audit = FakeAudit()
        use_cases = make_use_cases(link_service=link_service)

        result = await use_cases.create_link_token(user_id=7, audit=audit)

        assert result.token.link_token == "raw-token"
        assert link_service.link_tokens == [7]
        assert audit.logs == [
            {
                "action": "telegram.link_token_create",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"expires_at": EXPIRES_AT.isoformat()},
            }
        ]

    asyncio.run(scenario())


def test_unlink_account_logs_whether_user_had_telegram_id() -> None:
    async def scenario() -> None:
        link_service = FakeTelegramLinkService()
        audit = FakeAudit()
        use_cases = make_use_cases(link_service=link_service)

        result = await use_cases.unlink_account(
            actor=Actor(id=7, telegram_id=1001),
            audit=audit,
        )

        assert result.status.telegram_id is None
        assert link_service.unlinked_users == [7]
        assert audit.logs == [
            {
                "action": "telegram.unlink",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"had_telegram_id": True},
            }
        ]

    asyncio.run(scenario())


def test_create_subscription_writes_compact_audit_payload() -> None:
    async def scenario() -> None:
        subscription_service = FakeTelegramSubscriptionService()
        audit = FakeAudit()
        use_cases = make_use_cases(subscription_service=subscription_service)

        result = await use_cases.create_subscription(
            user_id=7,
            data=TelegramSubscriptionCreate(
                scope_type=TelegramScopeType.audience,
                scope_id=12,
                event_type=TelegramEventType.hardware_fault,
                delivery_mode=TelegramDeliveryMode.immediate,
            ),
            audit=audit,
        )

        assert result.subscription.id == 5
        assert subscription_service.created[0]["user_id"] == 7
        assert audit.logs == [
            {
                "action": "telegram.subscription_create",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {
                    "subscription_id": 5,
                    "scope_type": "audience",
                    "scope_id": 12,
                    "event_type": "hardware_fault",
                    "delivery_mode": "immediate",
                },
            }
        ]

    asyncio.run(scenario())


def test_delete_subscription_writes_audit() -> None:
    async def scenario() -> None:
        subscription_service = FakeTelegramSubscriptionService()
        audit = FakeAudit()
        use_cases = make_use_cases(subscription_service=subscription_service)

        await use_cases.delete_subscription(
            user_id=7,
            subscription_id=5,
            audit=audit,
        )

        assert subscription_service.deleted == [{"user_id": 7, "subscription_id": 5}]
        assert audit.logs == [
            {
                "action": "telegram.subscription_delete",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"subscription_id": 5},
            }
        ]

    asyncio.run(scenario())
