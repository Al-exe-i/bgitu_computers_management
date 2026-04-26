import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from core.exceptions import (
    TelegramAccountNotLinkedError,
    TelegramScopeInvalidError,
    TelegramScopeNotFoundError,
    TelegramSubscriptionAlreadyExistsError,
)
from schemas.telegram import (
    TelegramDeliveryMode,
    TelegramEventType,
    TelegramScopeType,
    TelegramSubscriptionCreate,
)
from services.telegram_subscription_service import TelegramSubscriptionService


class FakeTelegramSubscriptionRepo:
    def __init__(self) -> None:
        self.rows: dict[int, SimpleNamespace] = {}
        self.next_id = 1

    async def list_by_user(self, user_id: int):
        return [row for row in self.rows.values() if row.user_id == user_id]

    async def get_by_user_scope_and_event(self, *, user_id: int, scope_type: str, scope_id: int, event_type: str):
        for row in self.rows.values():
            if (
                row.user_id == user_id
                and row.scope_type == scope_type
                and row.scope_id == scope_id
                and row.event_type == event_type
            ):
                return row
        return None

    async def create(self, subscription: SimpleNamespace):
        subscription.id = self.next_id
        self.next_id += 1
        if getattr(subscription, "created_at", None) is None:
            subscription.created_at = datetime.now(timezone.utc)
        self.rows[subscription.id] = subscription
        return subscription

    async def get_by_user_and_id(self, *, user_id: int, subscription_id: int):
        row = self.rows.get(subscription_id)
        if row and row.user_id == user_id:
            return row
        return None

    async def delete(self, subscription: SimpleNamespace) -> None:
        self.rows.pop(subscription.id, None)


class FakeUserRepo:
    def __init__(self, users: dict[int, SimpleNamespace]) -> None:
        self.users = users

    async def get(self, user_id: int):
        return self.users.get(user_id)


class FakeAudienceRepo:
    def __init__(self, audience_ids: set[int]) -> None:
        self.audience_ids = audience_ids

    async def get_by_id(self, audience_id: int):
        if audience_id in self.audience_ids:
            return SimpleNamespace(id=audience_id)
        return None


class FakeOfficeRepo:
    def __init__(self, office_ids: set[int]) -> None:
        self.office_ids = office_ids

    async def get_one_short(self, office_id: int):
        if office_id in self.office_ids:
            return SimpleNamespace(id=office_id)
        return None


def make_user(
    *,
    user_id: int,
    linked: bool,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        telegram_id=123 if linked else None,
        telegram_id_confirmed=linked,
    )


def make_service(*, users: dict[int, SimpleNamespace], audience_ids: set[int], office_ids: set[int]):
    return TelegramSubscriptionService(
        FakeTelegramSubscriptionRepo(),
        FakeUserRepo(users),
        FakeAudienceRepo(audience_ids),
        FakeOfficeRepo(office_ids),
    )


def test_create_subscription_rejects_user_without_linked_telegram() -> None:
    async def scenario() -> None:
        service = make_service(
            users={7: make_user(user_id=7, linked=False)},
            audience_ids={10},
            office_ids=set(),
        )

        with pytest.raises(TelegramAccountNotLinkedError, match="not linked"):
            await service.create(
                user_id=7,
                data=TelegramSubscriptionCreate(
                    scope_type=TelegramScopeType.audience,
                    scope_id=10,
                    event_type=TelegramEventType.audience_changed,
                ),
            )

    asyncio.run(scenario())


def test_create_subscription_rejects_invalid_scope_event_pair() -> None:
    async def scenario() -> None:
        service = make_service(
            users={7: make_user(user_id=7, linked=True)},
            audience_ids={10},
            office_ids=set(),
        )

        with pytest.raises(TelegramScopeInvalidError, match="require user scope"):
            await service.create(
                user_id=7,
                data=TelegramSubscriptionCreate(
                    scope_type=TelegramScopeType.audience,
                    scope_id=10,
                    event_type=TelegramEventType.auth_security,
                ),
            )

    asyncio.run(scenario())


def test_create_subscription_creates_audience_subscription() -> None:
    async def scenario() -> None:
        service = make_service(
            users={7: make_user(user_id=7, linked=True)},
            audience_ids={10},
            office_ids=set(),
        )

        result = await service.create(
            user_id=7,
            data=TelegramSubscriptionCreate(
                scope_type=TelegramScopeType.audience,
                scope_id=10,
                event_type=TelegramEventType.hardware_fault,
                delivery_mode=TelegramDeliveryMode.immediate,
            ),
        )

        assert result.id == 1
        assert result.scope_type == TelegramScopeType.audience
        assert result.scope_id == 10
        assert result.event_type == TelegramEventType.hardware_fault

    asyncio.run(scenario())


def test_create_subscription_rejects_duplicates() -> None:
    async def scenario() -> None:
        service = make_service(
            users={7: make_user(user_id=7, linked=True)},
            audience_ids={10},
            office_ids=set(),
        )
        data = TelegramSubscriptionCreate(
            scope_type=TelegramScopeType.audience,
            scope_id=10,
            event_type=TelegramEventType.audience_changed,
        )

        await service.create(user_id=7, data=data)

        with pytest.raises(TelegramSubscriptionAlreadyExistsError, match="already exists"):
            await service.create(user_id=7, data=data)

    asyncio.run(scenario())


def test_create_subscription_rejects_missing_scope() -> None:
    async def scenario() -> None:
        service = make_service(
            users={7: make_user(user_id=7, linked=True)},
            audience_ids=set(),
            office_ids=set(),
        )

        with pytest.raises(TelegramScopeNotFoundError, match="Audience not found"):
            await service.create(
                user_id=7,
                data=TelegramSubscriptionCreate(
                    scope_type=TelegramScopeType.audience,
                    scope_id=99,
                    event_type=TelegramEventType.hardware_recovered,
                ),
            )

    asyncio.run(scenario())
