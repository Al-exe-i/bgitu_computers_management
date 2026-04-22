from typing import Annotated

from fastapi import Depends

from core.config import settings
from db.session import session_dep
from repositories.audience_repo import AudienceRepository
from repositories.office_repo import OfficeRepository
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from repositories.tg_link_token_repo import TelegramLinkTokenRepository
from repositories.user_repo import UserRepository
from services.telegram_link_service import TelegramLinkService
from services.telegram_subscription_service import TelegramSubscriptionService


def get_telegram_link_service(db: session_dep) -> TelegramLinkService:
    return TelegramLinkService(
        TelegramLinkTokenRepository(db),
        UserRepository(db),
        settings.telegram,
    )


def get_telegram_subscription_service(db: session_dep) -> TelegramSubscriptionService:
    return TelegramSubscriptionService(
        TelegramSubscriptionRepository(db),
        UserRepository(db),
        AudienceRepository(db),
        OfficeRepository(db),
    )


telegram_link_service_dep = Annotated[TelegramLinkService, Depends(get_telegram_link_service)]
telegram_subscription_service_dep = Annotated[
    TelegramSubscriptionService,
    Depends(get_telegram_subscription_service),
]
