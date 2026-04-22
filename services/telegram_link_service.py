from datetime import datetime, timedelta, timezone

from loguru import logger

from core.config import TelegramConfig
from core.exceptions import HTTP400, HTTP404, HTTP409
from models.tg_link_token import TelegramLinkToken
from repositories.tg_link_token_repo import TelegramLinkTokenRepository
from repositories.user_repo import UserRepository
from schemas.telegram import TelegramLinkStartResponse, TelegramLinkStatusResponse
from utils.telegram import (
    build_telegram_deep_link,
    hash_telegram_link_token,
    new_telegram_link_token,
)


class TelegramLinkService:
    def __init__(
        self,
        token_repo: TelegramLinkTokenRepository,
        user_repo: UserRepository,
        config: TelegramConfig,
    ) -> None:
        self.token_repo = token_repo
        self.user_repo = user_repo
        self.config = config

    async def get_link_status(self, user_id: int) -> TelegramLinkStatusResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTP404("User not found")

        telegram_id = str(user.telegram_id) if user.telegram_id is not None else None
        return TelegramLinkStatusResponse(
            telegram_id=telegram_id,
            telegram_id_confirmed=user.telegram_id_confirmed,
        )

    async def create_link_token(self, user_id: int) -> TelegramLinkStartResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTP404("User not found")

        await self.token_repo.deactivate_active_for_user(user_id)

        raw_token = new_telegram_link_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.config.link_token_ttl_minutes,
        )
        token = TelegramLinkToken(
            user_id=user_id,
            token_hash=hash_telegram_link_token(raw_token),
            expires_at=expires_at,
        )
        await self.token_repo.create(token)
        logger.info("Telegram link token created for user_id={}", user_id)

        return TelegramLinkStartResponse(
            link_token=raw_token,
            expires_at=expires_at,
            bot_username=self.config.bot_username,
            bot_deep_link=build_telegram_deep_link(
                bot_username=self.config.bot_username,
                token=raw_token,
            ),
        )

    async def confirm_link(
        self,
        *,
        token: str,
        telegram_id: int,
    ) -> TelegramLinkStatusResponse:
        link_token = await self.token_repo.get_active_by_token_hash_for_update(
            hash_telegram_link_token(token),
        )
        if not link_token:
            raise HTTP400("Telegram link token is invalid or expired")

        user = await self.user_repo.get(link_token.user_id)
        if not user:
            raise HTTP404("User not found")

        existing_user = await self.user_repo.get_by_telegram_id(telegram_id)
        if existing_user and existing_user.id != user.id:
            raise HTTP409("Telegram account is already linked to another user")

        await self.user_repo.set_telegram_link(user, telegram_id, confirmed=True)
        await self.token_repo.mark_used(link_token)
        logger.info("Telegram linked for user_id={} telegram_id={}", user.id, telegram_id)

        return TelegramLinkStatusResponse(
            telegram_id=str(telegram_id),
            telegram_id_confirmed=True,
        )

    async def unlink_user(self, user_id: int) -> TelegramLinkStatusResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTP404("User not found")

        await self.user_repo.clear_telegram_link(user)
        logger.info("Telegram unlinked for user_id={}", user_id)
        return TelegramLinkStatusResponse(
            telegram_id=None,
            telegram_id_confirmed=False,
        )
