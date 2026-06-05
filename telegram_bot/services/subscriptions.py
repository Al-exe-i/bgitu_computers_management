from dataclasses import dataclass

from core.exceptions import (
    TelegramAccountNotLinkedError,
    TelegramScopeInvalidError,
    TelegramScopeNotFoundError,
    TelegramSubscriptionAlreadyExistsError,
    TelegramSubscriptionNotFoundError,
)
from models.audience import Audience
from repositories.audience_repo import AudienceRepository
from repositories.office_repo import OfficeRepository
from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from repositories.user_repo import UserRepository
from schemas.telegram import (
    TelegramDeliveryMode,
    TelegramEventType,
    TelegramScopeType,
    TelegramSubscriptionCreate,
)
from services.telegram_subscription_service import TelegramSubscriptionService
from telegram_bot.db import open_session


@dataclass(slots=True)
class TelegramBotScopeOption:
    id: int
    label: str


class TelegramBotSubscriptionFacade:
    async def list_audience_options(self) -> list[TelegramBotScopeOption]:
        async with open_session() as session:
            rows = await AudienceRepository(session).list_short()
            return [self._build_audience_option(row) for row in rows]

    async def list_office_options(self) -> list[TelegramBotScopeOption]:
        async with open_session() as session:
            rows = await OfficeRepository(session).get_list_short()
            return [
                TelegramBotScopeOption(
                    id=row["id"],
                    label=self._truncate_label(
                        f"Корпус {row['id']} · {row['address']}"
                    ),
                )
                for row in rows
            ]

    async def create_subscription(
        self,
        *,
        telegram_id: int,
        scope_type: TelegramScopeType,
        scope_id: int,
        event_type: TelegramEventType,
    ) -> str:
        async with open_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user is None or not user.telegram_id_confirmed:
                return "not_linked"

            service = self._build_service(session)
            try:
                await service.create(
                    user_id=user.id,
                    data=TelegramSubscriptionCreate(
                        scope_type=scope_type,
                        scope_id=scope_id,
                        event_type=event_type,
                        delivery_mode=TelegramDeliveryMode.immediate,
                    ),
                )
            except TelegramSubscriptionAlreadyExistsError:
                return "exists"
            except (
                TelegramAccountNotLinkedError,
                TelegramScopeInvalidError,
                TelegramScopeNotFoundError,
            ):
                return "invalid"

            return "created"

    async def delete_subscription(
        self,
        *,
        telegram_id: int,
        subscription_id: int,
    ) -> str:
        async with open_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user is None or not user.telegram_id_confirmed:
                return "not_linked"

            service = self._build_service(session)
            try:
                await service.delete(
                    user_id=user.id,
                    subscription_id=subscription_id,
                )
            except TelegramSubscriptionNotFoundError:
                return "not_found"

            return "deleted"

    async def toggle_auth_security(self, *, telegram_id: int) -> str:
        async with open_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user is None or not user.telegram_id_confirmed:
                return "not_linked"

            repo = TelegramSubscriptionRepository(session)
            existing = await repo.get_by_user_scope_and_event(
                user_id=user.id,
                scope_type=TelegramScopeType.user.value,
                scope_id=user.id,
                event_type=TelegramEventType.auth_security.value,
            )
            service = self._build_service(session)

            if existing:
                await service.delete(
                    user_id=user.id,
                    subscription_id=existing.id,
                )
                return "disabled"

            await service.create(
                user_id=user.id,
                data=TelegramSubscriptionCreate(
                    scope_type=TelegramScopeType.user,
                    scope_id=user.id,
                    event_type=TelegramEventType.auth_security,
                    delivery_mode=TelegramDeliveryMode.immediate,
                ),
            )
            return "enabled"

    @staticmethod
    def _build_service(session) -> TelegramSubscriptionService:
        return TelegramSubscriptionService(
            TelegramSubscriptionRepository(session),
            UserRepository(session),
            AudienceRepository(session),
            OfficeRepository(session),
        )

    @staticmethod
    def _build_audience_option(audience: Audience) -> TelegramBotScopeOption:
        suffix = f" · {audience.description}" if audience.description else ""
        number = getattr(audience, "number", None) or audience.id
        label = (
            f"Ауд. {number} · корп. {audience.office_id} · этаж {audience.floor}"
            f"{suffix}"
        )
        return TelegramBotScopeOption(
            id=audience.id,
            label=TelegramBotSubscriptionFacade._truncate_label(label),
        )

    @staticmethod
    def _truncate_label(value: str, limit: int = 48) -> str:
        if len(value) <= limit:
            return value
        return value[: limit - 1].rstrip() + "…"
