from dataclasses import dataclass, field

from repositories.telegram_subscription_repo import TelegramSubscriptionRepository
from repositories.user_repo import UserRepository
from telegram_bot.db import open_session


@dataclass(slots=True)
class TelegramBotSubscriptionSnapshot:
    scope_type: str
    scope_id: int
    event_type: str
    delivery_mode: str
    enabled: bool
    id: int | None = None


@dataclass(slots=True)
class TelegramBotAccountSnapshot:
    is_linked: bool
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    subscriptions: list[TelegramBotSubscriptionSnapshot] = field(default_factory=list)


class TelegramBotAccountFacade:
    async def get_snapshot(self, *, telegram_id: int) -> TelegramBotAccountSnapshot:
        async with open_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if user is None or not user.telegram_id_confirmed:
                return TelegramBotAccountSnapshot(is_linked=False)

            subscription_repo = TelegramSubscriptionRepository(session)
            subscriptions = await subscription_repo.list_by_user(user.id)

            return TelegramBotAccountSnapshot(
                is_linked=True,
                email=user.email,
                full_name=self._build_full_name(user.name, user.surname),
                role=user.role.name,
                subscriptions=[
                    TelegramBotSubscriptionSnapshot(
                        id=subscription.id,
                        scope_type=subscription.scope_type,
                        scope_id=subscription.scope_id,
                        event_type=subscription.event_type,
                        delivery_mode=subscription.delivery_mode,
                        enabled=subscription.enabled,
                    )
                    for subscription in subscriptions
                ],
            )

    @staticmethod
    def _build_full_name(name: str | None, surname: str | None) -> str | None:
        parts = [part for part in [surname, name] if part]
        return " ".join(parts) if parts else None
