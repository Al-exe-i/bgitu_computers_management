class IdentityError(Exception):
    detail = "Identity operation failed"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class UserNotFoundError(IdentityError):
    detail = "User not found"


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


class InviteError(IdentityError):
    detail = "Invite operation failed"


class InviteBatchInputError(InviteError):
    detail = "Either count or emails must be provided"


class InviteNotFoundError(InviteError):
    detail = "Invite not found"


class InviteAlreadyUsedError(InviteError):
    detail = "Invite already used"


class InviteInvalidError(InviteError):
    detail = "Invite is invalid, expired, revoked or already used"


class InviteAssignedToAnotherEmailError(InviteError):
    detail = "This invite is assigned to another email"


class InviteUserAlreadyExistsError(InviteError):
    detail = "User with this email already exists"
