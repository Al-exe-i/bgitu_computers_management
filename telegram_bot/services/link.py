from core.config import settings
from core.exceptions import HTTP400, HTTP409
from repositories.tg_link_token_repo import TelegramLinkTokenRepository
from repositories.user_repo import UserRepository
from schemas.telegram import TelegramLinkStatusResponse
from services.telegram_link_service import TelegramLinkService
from telegram_bot.db import open_session


class TelegramBotLinkFacade:
    async def confirm_link(
        self,
        *,
        token: str,
        telegram_id: int,
    ) -> TelegramLinkStatusResponse:
        async with open_session() as session:
            service = TelegramLinkService(
                TelegramLinkTokenRepository(session),
                UserRepository(session),
                settings.telegram,
            )
            return await service.confirm_link(token=token, telegram_id=telegram_id)

    @staticmethod
    def classify_error(exc: Exception) -> str:
        if isinstance(exc, HTTP409):
            return "conflict"
        if isinstance(exc, HTTP400):
            return "invalid"
        return "generic"
