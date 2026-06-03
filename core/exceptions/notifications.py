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


class TelegramNotificationAudienceNotFoundError(NotificationError):
    detail = "Audience not found"


class NotificationUserNotFoundError(NotificationError):
    detail = "User not found"


class NotificationSubscriptionAlreadyExistsError(NotificationError):
    detail = "Notification subscription already exists"


class NotificationSubscriptionNotFoundError(NotificationError):
    detail = "Notification subscription not found"


class NotificationScopeInvalidError(NotificationError):
    detail = "Notification subscription scope is invalid"


class NotificationScopeNotFoundError(NotificationError):
    detail = "Notification subscription scope not found"


class NotificationAudienceNotFoundError(NotificationError):
    detail = "Audience not found"
