from loguru import logger

from core.exceptions import (
    NotificationScopeInvalidError,
    NotificationScopeNotFoundError,
    NotificationSubscriptionAlreadyExistsError,
    NotificationSubscriptionNotFoundError,
    NotificationUserNotFoundError,
)
from models.notification_subscription import NotificationSubscription
from repositories.audience_repo import AudienceRepository
from repositories.notification_subscription_repo import NotificationSubscriptionRepository
from repositories.office_repo import OfficeRepository
from repositories.user_repo import UserRepository
from schemas.notification import (
    NotificationEventType,
    NotificationScopeType,
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)


class NotificationSubscriptionService:
    def __init__(
        self,
        repo: NotificationSubscriptionRepository,
        user_repo: UserRepository,
        audience_repo: AudienceRepository,
        office_repo: OfficeRepository,
    ) -> None:
        self.repo = repo
        self.user_repo = user_repo
        self.audience_repo = audience_repo
        self.office_repo = office_repo

    async def list_for_user(self, user_id: int) -> list[NotificationSubscriptionResponse]:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotificationUserNotFoundError()

        rows = await self.repo.list_by_user(user_id)
        return [
            NotificationSubscriptionResponse.model_validate(row, from_attributes=True)
            for row in rows
        ]

    async def create(
        self,
        *,
        user_id: int,
        data: NotificationSubscriptionCreate,
    ) -> NotificationSubscriptionResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotificationUserNotFoundError()

        self._validate_scope_event(user_id=user_id, data=data)
        await self._validate_scope_exists(data)

        existing = await self.repo.get_by_user_scope_and_event(
            user_id=user_id,
            scope_type=data.scope_type.value,
            scope_id=data.scope_id,
            event_type=data.event_type.value,
        )
        if existing:
            raise NotificationSubscriptionAlreadyExistsError()

        subscription = NotificationSubscription(
            user_id=user_id,
            scope_type=data.scope_type.value,
            scope_id=data.scope_id,
            event_type=data.event_type.value,
            enabled=True,
        )
        created = await self.repo.create(subscription)
        logger.info(
            "Notification subscription created: user_id={} scope_type={} scope_id={} event_type={}",
            user_id,
            data.scope_type.value,
            data.scope_id,
            data.event_type.value,
        )
        return NotificationSubscriptionResponse.model_validate(created, from_attributes=True)

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
            raise NotificationSubscriptionNotFoundError()

        await self.repo.delete(subscription)
        logger.info(
            "Notification subscription deleted: user_id={} subscription_id={}",
            user_id,
            subscription_id,
        )

    @staticmethod
    def _validate_scope_event(
        *,
        user_id: int,
        data: NotificationSubscriptionCreate,
    ) -> None:
        if data.scope_type == NotificationScopeType.user:
            if data.scope_id != user_id:
                raise NotificationScopeInvalidError("User scope can target only the current user")
            if data.event_type != NotificationEventType.auth_security:
                raise NotificationScopeInvalidError("User scope supports only auth_security notifications")
            return

        if data.event_type == NotificationEventType.auth_security:
            raise NotificationScopeInvalidError("auth_security notifications require user scope")

    async def _validate_scope_exists(self, data: NotificationSubscriptionCreate) -> None:
        if data.scope_type == NotificationScopeType.audience:
            audience = await self.audience_repo.get_one_short(data.scope_id)
            if audience is None:
                raise NotificationScopeNotFoundError("Audience not found")
            return

        if data.scope_type == NotificationScopeType.office:
            office = await self.office_repo.get_one_short(data.scope_id)
            if office is None:
                raise NotificationScopeNotFoundError("Office not found")
            return
