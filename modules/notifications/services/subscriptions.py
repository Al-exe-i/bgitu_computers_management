from loguru import logger

from core.exceptions import (
    NotificationScopeInvalidError,
    NotificationScopeNotFoundError,
    NotificationSubscriptionAlreadyExistsError,
    NotificationSubscriptionNotFoundError,
    NotificationUserNotFoundError,
)
from modules.identity.public import UserDirectory
from modules.inventory.public import AudienceDirectory, OfficeDirectory
from modules.notifications.models.subscription import NotificationSubscription
from modules.notifications.repositories.subscriptions import (
    NotificationSubscriptionRepository,
)
from modules.notifications.schemas import (
    NotificationEventType,
    NotificationScopeType,
    NotificationSubscriptionCreate,
    NotificationSubscriptionResponse,
)


class NotificationSubscriptionService:
    def __init__(
        self,
        repo: NotificationSubscriptionRepository,
        users: UserDirectory,
        audiences: AudienceDirectory,
        offices: OfficeDirectory,
    ) -> None:
        self.repo = repo
        self.users = users
        self.audiences = audiences
        self.offices = offices

    async def list_for_user(self, user_id: int) -> list[NotificationSubscriptionResponse]:
        if not await self.users.exists(user_id):
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
        if not await self.users.exists(user_id):
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
            audience = await self.audiences.get_one_short(data.scope_id)
            if audience is None:
                raise NotificationScopeNotFoundError("Audience not found")
            return

        if data.scope_type == NotificationScopeType.office:
            office = await self.offices.get_one_short(data.scope_id)
            if office is None:
                raise NotificationScopeNotFoundError("Office not found")
            return
