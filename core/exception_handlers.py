from collections.abc import Awaitable, Callable
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    AudienceAlreadyExistsError,
    AudienceGridValidationError,
    AudienceNotFoundError,
    HardwareFileBadRangeError,
    HardwareFileMissingOnDiskError,
    HardwareFileNotFoundError,
    HardwareFileRangeNotSatisfiableError,
    HardwareFileUnsupportedMediaError,
    HardwareNotFoundError,
    HardwarePermissionDeniedError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidUserPhotoError,
    InviteAlreadyUsedError,
    InviteAssignedToAnotherEmailError,
    InviteBatchInputError,
    InviteInvalidError,
    InviteNotFoundError,
    InviteUserAlreadyExistsError,
    NotificationAudienceNotFoundError,
    NotificationScopeInvalidError,
    NotificationScopeNotFoundError,
    NotificationSubscriptionAlreadyExistsError,
    NotificationSubscriptionNotFoundError,
    NotificationUserNotFoundError,
    OfficeAlreadyExistsError,
    OfficeNotFoundError,
    RefreshSessionNotFoundError,
    RefreshTokenMissingError,
    RefreshTokenReuseDetectedError,
    RefreshUserNotFoundError,
    SamePasswordError,
    SelfDeleteForbiddenError,
    SessionNotFoundError,
    SuperuserDeleteForbiddenError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserPermissionDeniedError,
    UploadTooLargeError,
)


ExceptionHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]


DOMAIN_EXCEPTION_STATUS: dict[type[Exception], int] = {
    InvalidCredentialsError: HTTPStatus.UNAUTHORIZED,
    RefreshTokenMissingError: HTTPStatus.UNAUTHORIZED,
    RefreshSessionNotFoundError: HTTPStatus.UNAUTHORIZED,
    RefreshUserNotFoundError: HTTPStatus.UNAUTHORIZED,
    RefreshTokenReuseDetectedError: HTTPStatus.UNAUTHORIZED,
    SessionNotFoundError: HTTPStatus.NOT_FOUND,
    InvalidCurrentPasswordError: HTTPStatus.BAD_REQUEST,
    SamePasswordError: HTTPStatus.BAD_REQUEST,
    SelfDeleteForbiddenError: HTTPStatus.BAD_REQUEST,
    SuperuserDeleteForbiddenError: HTTPStatus.BAD_REQUEST,
    InvalidUserPhotoError: HTTPStatus.BAD_REQUEST,
    UserPermissionDeniedError: HTTPStatus.FORBIDDEN,
    UserNotFoundError: HTTPStatus.NOT_FOUND,
    InviteBatchInputError: HTTPStatus.BAD_REQUEST,
    InviteAlreadyUsedError: HTTPStatus.BAD_REQUEST,
    InviteInvalidError: HTTPStatus.BAD_REQUEST,
    InviteAssignedToAnotherEmailError: HTTPStatus.BAD_REQUEST,
    InviteNotFoundError: HTTPStatus.NOT_FOUND,
    InviteUserAlreadyExistsError: HTTPStatus.CONFLICT,
    UserAlreadyExistsError: HTTPStatus.CONFLICT,
    NotificationUserNotFoundError: HTTPStatus.NOT_FOUND,
    NotificationSubscriptionAlreadyExistsError: HTTPStatus.CONFLICT,
    NotificationSubscriptionNotFoundError: HTTPStatus.NOT_FOUND,
    NotificationScopeInvalidError: HTTPStatus.BAD_REQUEST,
    NotificationScopeNotFoundError: HTTPStatus.NOT_FOUND,
    NotificationAudienceNotFoundError: HTTPStatus.NOT_FOUND,
    AudienceAlreadyExistsError: HTTPStatus.CONFLICT,
    AudienceGridValidationError: HTTPStatus.BAD_REQUEST,
    AudienceNotFoundError: HTTPStatus.NOT_FOUND,
    HardwareNotFoundError: HTTPStatus.NOT_FOUND,
    HardwarePermissionDeniedError: HTTPStatus.FORBIDDEN,
    HardwareFileNotFoundError: HTTPStatus.NOT_FOUND,
    HardwareFileMissingOnDiskError: HTTPStatus.NOT_FOUND,
    HardwareFileUnsupportedMediaError: HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
    HardwareFileBadRangeError: HTTPStatus.BAD_REQUEST,
    HardwareFileRangeNotSatisfiableError: HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
    OfficeAlreadyExistsError: HTTPStatus.CONFLICT,
    OfficeNotFoundError: HTTPStatus.NOT_FOUND,
    UploadTooLargeError: HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exception_class in DOMAIN_EXCEPTION_STATUS:
        app.add_exception_handler(exception_class, domain_exception_handler)  # type: ignore[arg-type]


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = _status_code(exc)
    return JSONResponse(
        status_code=int(status_code),
        content={"detail": _exception_detail(exc)},
    )


def _status_code(exc: Exception) -> int:
    for exception_class in type(exc).__mro__:
        status_code = DOMAIN_EXCEPTION_STATUS.get(exception_class)
        if status_code is not None:
            return int(status_code)
    return int(HTTPStatus.BAD_REQUEST)


def _exception_detail(exc: Exception) -> str:
    return str(exc) or str(getattr(exc, "detail", "Request failed"))
