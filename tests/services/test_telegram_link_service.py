import asyncio
from types import SimpleNamespace

import pytest

from core.config import TelegramConfig
from core.exceptions import TelegramAccountAlreadyLinkedError, TelegramLinkTokenInvalidError
from services.telegram_link_service import TelegramLinkService
from utils.telegram import hash_telegram_link_token


class FakeTelegramLinkTokenRepo:
    def __init__(self) -> None:
        self.deactivated_user_ids: list[int] = []
        self.tokens_by_hash: dict[str, SimpleNamespace] = {}
        self.used_tokens: list[str] = []

    async def deactivate_active_for_user(self, user_id: int) -> None:
        self.deactivated_user_ids.append(user_id)

    async def create(self, token: SimpleNamespace) -> SimpleNamespace:
        self.tokens_by_hash[token.token_hash] = token
        return token

    async def get_active_by_token_hash_for_update(self, token_hash: str):
        return self.tokens_by_hash.get(token_hash)

    async def mark_used(self, token: SimpleNamespace) -> None:
        self.used_tokens.append(token.token_hash)


class FakeUserRepo:
    def __init__(self, users: dict[int, SimpleNamespace]) -> None:
        self.users = users
        self.link_updates: list[tuple[int, int, bool]] = []
        self.cleared_users: list[int] = []

    async def get(self, user_id: int):
        return self.users.get(user_id)

    async def get_by_telegram_id(self, telegram_id: int):
        for user in self.users.values():
            if user.telegram_id == telegram_id:
                return user
        return None

    async def set_telegram_link(self, user, telegram_id: int, *, confirmed: bool):
        user.telegram_id = telegram_id
        user.telegram_id_confirmed = confirmed
        self.link_updates.append((user.id, telegram_id, confirmed))
        return user

    async def clear_telegram_link(self, user):
        user.telegram_id = None
        user.telegram_id_confirmed = False
        self.cleared_users.append(user.id)
        return user


def make_user(
    *,
    user_id: int,
    telegram_id: int | None = None,
    telegram_id_confirmed: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        telegram_id=telegram_id,
        telegram_id_confirmed=telegram_id_confirmed,
    )


def test_create_link_token_builds_deep_link_and_rotates_old_tokens() -> None:
    async def scenario() -> None:
        token_repo = FakeTelegramLinkTokenRepo()
        user_repo = FakeUserRepo({7: make_user(user_id=7)})
        service = TelegramLinkService(
            token_repo,
            user_repo,
            TelegramConfig(
                enabled=True,
                bot_username="bgitu_test_bot",
                link_token_ttl_minutes=15,
            ),
        )

        result = await service.create_link_token(7)

        assert token_repo.deactivated_user_ids == [7]
        assert result.bot_username == "bgitu_test_bot"
        assert result.bot_deep_link == (
            f"https://t.me/bgitu_test_bot?start=link_{result.link_token}"
        )
        assert hash_telegram_link_token(result.link_token) in token_repo.tokens_by_hash

    asyncio.run(scenario())


def test_confirm_link_marks_token_used_and_links_user() -> None:
    async def scenario() -> None:
        raw_token = "raw-token"
        token_hash = hash_telegram_link_token(raw_token)
        token_repo = FakeTelegramLinkTokenRepo()
        token_repo.tokens_by_hash[token_hash] = SimpleNamespace(
            user_id=7,
            token_hash=token_hash,
        )
        user_repo = FakeUserRepo({7: make_user(user_id=7)})
        service = TelegramLinkService(
            token_repo,
            user_repo,
            TelegramConfig(enabled=True),
        )

        result = await service.confirm_link(token=raw_token, telegram_id=123456789)

        assert result.telegram_id == "123456789"
        assert result.telegram_id_confirmed is True
        assert user_repo.link_updates == [(7, 123456789, True)]
        assert token_repo.used_tokens == [token_hash]

    asyncio.run(scenario())


def test_confirm_link_rejects_token_bound_to_another_user() -> None:
    async def scenario() -> None:
        raw_token = "raw-token"
        token_hash = hash_telegram_link_token(raw_token)
        token_repo = FakeTelegramLinkTokenRepo()
        token_repo.tokens_by_hash[token_hash] = SimpleNamespace(
            user_id=7,
            token_hash=token_hash,
        )
        user_repo = FakeUserRepo(
            {
                7: make_user(user_id=7),
                8: make_user(user_id=8, telegram_id=123456789, telegram_id_confirmed=True),
            }
        )
        service = TelegramLinkService(
            token_repo,
            user_repo,
            TelegramConfig(enabled=True),
        )

        with pytest.raises(TelegramAccountAlreadyLinkedError, match="already linked"):
            await service.confirm_link(token=raw_token, telegram_id=123456789)

    asyncio.run(scenario())


def test_confirm_link_rejects_invalid_token() -> None:
    async def scenario() -> None:
        service = TelegramLinkService(
            FakeTelegramLinkTokenRepo(),
            FakeUserRepo({7: make_user(user_id=7)}),
            TelegramConfig(enabled=True),
        )

        with pytest.raises(TelegramLinkTokenInvalidError, match="invalid or expired"):
            await service.confirm_link(token="missing", telegram_id=123)

    asyncio.run(scenario())
