from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Query
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from core.exceptions import (
    HTTP401,
    HTTP404,
    InvalidCredentialsError,
    RefreshSessionNotFoundError,
    RefreshTokenMissingError,
    RefreshTokenReuseDetectedError,
    RefreshUserNotFoundError,
    SessionNotFoundError,
)
from dependencies.auth_service import auth_service_dep
from dependencies.audit_actor import audit_ctx_dep, user_audit_actor_dep
from dependencies.invite import invite_service_dep
from dependencies.user import user_service_dep
from schemas.invite import (
    InvitePreviewRequest,
    InvitePreviewResponse,
    RegisterByInviteRequest,
    RegisterByInviteResponse,
)
from schemas.user_session import UserSessionOut
from utils.tokens import build_token_response
from utils.telegram_notifications import enqueue_auth_security_notification

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    background_tasks: BackgroundTasks,
    auth_service: auth_service_dep,
    audit: audit_ctx_dep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        result = await auth_service.login(
            email=form_data.username,
            password=form_data.password,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
        )
    except InvalidCredentialsError:
        raise HTTP401("Invalid credentials")

    await audit.log(
        action="auth.login",
        entity_type="user",
        entity_id=result.user_id,
        payload={"email": result.user_email, "sid": result.sid},
        user_id=result.user_id,
    )
    enqueue_auth_security_notification(
        background_tasks,
        user_id=result.user_id,
        event_name="Выполнен вход в аккаунт",
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
    )

    return build_token_response(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post("/refresh")
async def refresh_tokens(
    auth_service: auth_service_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    try:
        result = await auth_service.refresh(
            refresh_token=refresh_token,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
        )
    except RefreshTokenMissingError:
        raise HTTP401("No refresh token provided")
    except RefreshSessionNotFoundError:
        raise HTTP401("Couldn't validate refresh token")
    except RefreshUserNotFoundError:
        raise HTTP401("User not found")
    except RefreshTokenReuseDetectedError as exc:
        await audit.log(
            action="auth.refresh_reuse",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": exc.sid},
            user_id=exc.user_id,
        )
        raise HTTP401("Refresh token revoked")

    await audit.log(
        action="auth.refresh",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": result.sid},
        user_id=result.user_id,
    )

    return build_token_response(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post("/logout")
async def logout_user(
    response: Response,
    auth_service: auth_service_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    result = await auth_service.logout(
        refresh_token=refresh_token,
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
    )

    if result.user_id:
        await audit.log(
            action="auth.logout",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": result.sid},
            user_id=result.user_id,
        )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.post("/logout_all")
async def logout_all_user_sessions(
    background_tasks: BackgroundTasks,
    response: Response,
    auth_service: auth_service_dep,
    audit: user_audit_actor_dep,
):
    user_id = audit.user.id

    await auth_service.logout_all(user_id=user_id)

    await audit.log(
        action="auth.logout_all",
        entity_type="user_session",
        entity_id=None,
        payload={"user_id": user_id},
    )
    enqueue_auth_security_notification(
        background_tasks,
        user_id=user_id,
        event_name="Выполнен выход на всех устройствах",
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
    )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.get("/sessions", response_model=list[UserSessionOut])
async def get_my_sessions(
    auth_service: auth_service_dep,
    audit: user_audit_actor_dep,
    include_inactive: bool = Query(False),
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    return await auth_service.list_user_sessions(
        user_id=audit.user.id,
        include_inactive=include_inactive,
        refresh_token=refresh_token,
    )


@router.delete("/sessions/{sid}", status_code=HTTPStatus.NO_CONTENT)
async def revoke_session(
    sid: str,
    response: Response,
    auth_service: auth_service_dep,
    audit: user_audit_actor_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    try:
        result = await auth_service.revoke_session(
            user_id=audit.user.id,
            sid=sid,
            refresh_token=refresh_token,
        )
    except SessionNotFoundError:
        raise HTTP404("Session not found")

    await audit.log(
        action="auth.session_revoke",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": sid},
    )

    if result.revoked_current_session:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")


@router.post("/auth/invite/preview", response_model=InvitePreviewResponse)
async def preview_invite(
    data: InvitePreviewRequest,
    service: invite_service_dep,
):
    return await service.preview(data.token)


@router.post("/auth/invite/register", response_model=RegisterByInviteResponse)
async def register_by_invite(
    data: RegisterByInviteRequest,
    service: invite_service_dep,
    user_service: user_service_dep,
    audit: audit_ctx_dep,
):
    result = await service.register_by_invite(
        data,
        get_user_by_email=user_service.get_by_email,
        create_user=user_service.create,
    )

    await audit.log(
        action="auth.register_by_invite",
        entity_type="user",
        entity_id=result.user_id,
        payload={"email": result.email, "role": result.role},
        user_id=result.user_id,
    )

    return result
