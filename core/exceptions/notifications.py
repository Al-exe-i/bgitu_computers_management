class NotificationError(Exception):
    detail = "Notification operation failed"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


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
