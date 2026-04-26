from loguru import logger

from core.exceptions import (
    TelegramAccountNotLinkedError,
    TelegramScopeInvalidError,
    TelegramScopeNotFoundError,
    TelegramSubscriptionAlreadyExistsError,
    TelegramSubscriptionNotFoundError,
    TelegramUserNotFoundError,
)
from models.telegram_subscription import TelegramSubscription
from repositories.audience_repo import AudienceRepository
from repositories.office_repo import OfficeRepository
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from repositories.user_repo import UserRepository
from schemas.telegram import (
    TelegramEventType,
    TelegramScopeType,
    TelegramSubscriptionCreate,
    TelegramSubscriptionResponse,
)


class TelegramSubscriptionService:
    def __init__(
        self,
        repo: TelegramSubscriptionRepository,
        user_repo: UserRepository,
        audience_repo: AudienceRepository,
        office_repo: OfficeRepository,
    ) -> None:
        self.repo = repo
        self.user_repo = user_repo
        self.audience_repo = audience_repo
        self.office_repo = office_repo

    async def list_for_user(self, user_id: int) -> list[TelegramSubscriptionResponse]:
        user = await self.user_repo.get(user_id)
        if not user:
            raise TelegramUserNotFoundError()

        rows = await self.repo.list_by_user(user_id)
        return [
            TelegramSubscriptionResponse.model_validate(row, from_attributes=True)
            for row in rows
        ]

    async def create(
        self,
        *,
        user_id: int,
        data: TelegramSubscriptionCreate,
    ) -> TelegramSubscriptionResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise TelegramUserNotFoundError()

        if user.telegram_id is None or not user.telegram_id_confirmed:
            raise TelegramAccountNotLinkedError()

        self._validate_scope_event(user_id=user_id, data=data)
        await self._validate_scope_exists(data)

        existing = await self.repo.get_by_user_scope_and_event(
            user_id=user_id,
            scope_type=data.scope_type.value,
            scope_id=data.scope_id,
            event_type=data.event_type.value,
        )
        if existing:
            raise TelegramSubscriptionAlreadyExistsError()

        subscription = TelegramSubscription(
            user_id=user_id,
            scope_type=data.scope_type.value,
            scope_id=data.scope_id,
            event_type=data.event_type.value,
            delivery_mode=data.delivery_mode.value,
            enabled=True,
        )
        created = await self.repo.create(subscription)
        logger.info(
            "Telegram subscription created: user_id={} scope_type={} scope_id={} event_type={}",
            user_id,
            data.scope_type.value,
            data.scope_id,
            data.event_type.value,
        )
        return TelegramSubscriptionResponse.model_validate(created, from_attributes=True)

    async def delete(
        self,
        *,
        user_id: int,
        subscription_id: int,
    ) -> None:
        subscription = await self.repo.get_by_user_and_id(
            user_id=user_id,
            subscription_id=subscription_id,
        )
        if not subscription:
            raise TelegramSubscriptionNotFoundError()

        await self.repo.delete(subscription)
        logger.info(
            "Telegram subscription deleted: user_id={} subscription_id={}",
            user_id,
            subscription_id,
        )

    @staticmethod
    def _validate_scope_event(
        *,
        user_id: int,
        data: TelegramSubscriptionCreate,
    ) -> None:
        if data.scope_type == TelegramScopeType.user:
            if data.scope_id != user_id:
                raise TelegramScopeInvalidError("User scope can target only the current user")
            if data.event_type != TelegramEventType.auth_security:
                raise TelegramScopeInvalidError("User scope supports only auth_security notifications")
            return

        if data.event_type == TelegramEventType.auth_security:
            raise TelegramScopeInvalidError("auth_security notifications require user scope")

    async def _validate_scope_exists(self, data: TelegramSubscriptionCreate) -> None:
        if data.scope_type == TelegramScopeType.audience:
            audience = await self.audience_repo.get_by_id(data.scope_id)
            if audience is None:
                raise TelegramScopeNotFoundError("Audience not found")
            return

        if data.scope_type == TelegramScopeType.office:
            office = await self.office_repo.get_one_short(data.scope_id)
            if office is None:
                raise TelegramScopeNotFoundError("Office not found")
