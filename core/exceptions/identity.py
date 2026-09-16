class IdentityError(Exception):
    detail = "Identity operation failed"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class UserNotFoundError(IdentityError):
    detail = "User not found"


class UserAlreadyExistsError(IdentityError):
    detail = "User already exists"


class UserPermissionDeniedError(IdentityError):
    detail = "Not enough permissions"


class InvalidCurrentPasswordError(IdentityError):
    detail = "Неверный текущий пароль"


class SamePasswordError(IdentityError):
    detail = "Новый пароль не должен совпадать со старым"


class SelfDeleteForbiddenError(IdentityError):
    detail = "You can't delete yourself"


class SuperuserDeleteForbiddenError(IdentityError):
    detail = "You can't delete superuser"


class InvalidUserPhotoError(IdentityError):
    detail = "File must be an image"
