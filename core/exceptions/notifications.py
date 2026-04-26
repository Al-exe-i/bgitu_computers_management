class NotificationError(Exception):
    detail = "Notification operation failed"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class TelegramUserNotFoundError(NotificationError):
    detail = "User not found"


class TelegramLinkTokenInvalidError(NotificationError):
    detail = "Telegram link token is invalid or expired"


class TelegramAccountAlreadyLinkedError(NotificationError):
    detail = "Telegram account is already linked to another user"


class TelegramAccountNotLinkedError(NotificationError):
    detail = "Telegram account is not linked"


class TelegramSubscriptionAlreadyExistsError(NotificationError):
    detail = "Telegram subscription already exists"


class TelegramSubscriptionNotFoundError(NotificationError):
    detail = "Telegram subscription not found"


class TelegramScopeInvalidError(NotificationError):
    detail = "Telegram subscription scope is invalid"


class TelegramScopeNotFoundError(NotificationError):
    detail = "Telegram subscription scope not found"
