import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

from core.exceptions import TelegramSubscriptionAlreadyExistsError
from schemas.telegram import TelegramEventType, TelegramScopeType
from telegram_bot.services.subscriptions import TelegramBotSubscriptionFacade


class FakeUserRepo:
    def __init__(self, _session) -> None:
        pass

    async def get_by_telegram_id(self, telegram_id: int):
        if telegram_id == 0:
            return None
        return SimpleNamespace(id=5, telegram_id_confirmed=True)


class FakeSubscriptionRepoExisting:
    def __init__(self, _session) -> None:
        pass

    async def get_by_user_scope_and_event(self, **_kwargs):
        return SimpleNamespace(id=11)


class FakeSubscriptionRepoMissing:
    def __init__(self, _session) -> None:
        pass

    async def get_by_user_scope_and_event(self, **_kwargs):
        return None


def test_toggle_auth_security_disables_existing_subscription(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    class FakeService:
        async def delete(self, **kwargs):
            calls.append(("delete", kwargs))

    @asynccontextmanager
    async def fake_open_session():
        yield object()

    monkeypatch.setattr("telegram_bot.services.subscriptions.open_session", fake_open_session)
    monkeypatch.setattr("telegram_bot.services.subscriptions.UserRepository", FakeUserRepo)
    monkeypatch.setattr(
        "telegram_bot.services.subscriptions.TelegramSubscriptionRepository",
        FakeSubscriptionRepoExisting,
    )
    monkeypatch.setattr(
        TelegramBotSubscriptionFacade,
        "_build_service",
        staticmethod(lambda _session: FakeService()),
    )

    result = asyncio.run(TelegramBotSubscriptionFacade().toggle_auth_security(telegram_id=1001))

    assert result == "disabled"
    assert calls == [("delete", {"user_id": 5, "subscription_id": 11})]


def test_toggle_auth_security_enables_subscription_when_missing(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    class FakeService:
        async def create(self, **kwargs):
            calls.append(("create", kwargs))

    @asynccontextmanager
    async def fake_open_session():
        yield object()

    monkeypatch.setattr("telegram_bot.services.subscriptions.open_session", fake_open_session)
    monkeypatch.setattr("telegram_bot.services.subscriptions.UserRepository", FakeUserRepo)
    monkeypatch.setattr(
        "telegram_bot.services.subscriptions.TelegramSubscriptionRepository",
        FakeSubscriptionRepoMissing,
    )
    monkeypatch.setattr(
        TelegramBotSubscriptionFacade,
        "_build_service",
        staticmethod(lambda _session: FakeService()),
    )

    result = asyncio.run(TelegramBotSubscriptionFacade().toggle_auth_security(telegram_id=1001))

    assert result == "enabled"
    assert calls[0][0] == "create"
    assert calls[0][1]["user_id"] == 5
    assert calls[0][1]["data"].scope_type == TelegramScopeType.user
    assert calls[0][1]["data"].scope_id == 5
    assert calls[0][1]["data"].event_type == TelegramEventType.auth_security


def test_create_subscription_returns_exists_for_duplicates(monkeypatch) -> None:
    class FakeService:
        async def create(self, **_kwargs):
            raise TelegramSubscriptionAlreadyExistsError("exists")

    @asynccontextmanager
    async def fake_open_session():
        yield object()

    monkeypatch.setattr("telegram_bot.services.subscriptions.open_session", fake_open_session)
    monkeypatch.setattr("telegram_bot.services.subscriptions.UserRepository", FakeUserRepo)
    monkeypatch.setattr(
        TelegramBotSubscriptionFacade,
        "_build_service",
        staticmethod(lambda _session: FakeService()),
    )

    result = asyncio.run(
        TelegramBotSubscriptionFacade().create_subscription(
            telegram_id=1001,
            scope_type=TelegramScopeType.audience,
            scope_id=215,
            event_type=TelegramEventType.hardware_fault,
        )
    )

    assert result == "exists"
