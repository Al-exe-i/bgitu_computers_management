from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Cookie, Depends, Query
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from core.exceptions import HTTP401, HTTP404
from core.security import verify_password
from dependencies.audit_actor import audit_ctx_dep, user_audit_actor_dep
from dependencies.invite import invite_service_dep
from dependencies.user import user_service_dep
from dependencies.user_session_service import user_session_service_dep
from schemas.invite import (
    InvitePreviewRequest,
    InvitePreviewResponse,
    RegisterByInviteRequest,
    RegisterByInviteResponse,
)
from schemas.user_session import UserSessionOut
from utils.tokens import (
    build_token_response,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
)

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    service: user_service_dep,
    sessions: user_session_service_dep,
    audit: audit_ctx_dep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await service.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTP401("Invalid credentials")

    sid = sessions.new_sid()
    refresh_token = new_refresh_token()

    await sessions.create_session(
        user_id=user.id,
        sid=sid,
        refresh_token_hash=hash_refresh_token(refresh_token),
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
    )

    access_token = issue_access_token(user.id)

    await audit.log(
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        payload={"email": user.email, "sid": sid},
        user_id=user.id,
    )

    return build_token_response(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh")
async def refresh_tokens(
    service: user_service_dep,
    sessions: user_session_service_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    if not refresh_token:
        raise HTTP401("No refresh token provided")

    session = await sessions.get_active_by_refresh_token(refresh_token)
    if not session:
        raise HTTP401("Couldn't validate refresh token")

    user = await service.get(session.user_id)
    if not user:
        await sessions.revoke(session.sid)
        raise HTTP401("User not found")

    new_token = new_refresh_token()
    rotated = await sessions.rotate_refresh_token(
        sid=session.sid,
        old_refresh_token=refresh_token,
        new_refresh_token=new_token,
    )
    if not rotated:
        await sessions.revoke(session.sid)

        await audit.log(
            action="auth.refresh_reuse",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": session.sid},
            user_id=user.id,
        )
        raise HTTP401("Refresh token revoked")

    access_token = issue_access_token(user.id)

    await audit.log(
        action="auth.refresh",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": session.sid},
        user_id=user.id,
    )

    return build_token_response(
        access_token=access_token,
        refresh_token=new_token,
    )


@router.post("/logout")
async def logout_user(
    response: Response,
    sessions: user_session_service_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    sid = None
    user_id = None

    if refresh_token:
        session = await sessions.get_active_by_refresh_token(refresh_token)
        if session:
            sid = session.sid
            user_id = session.user_id
            await sessions.revoke(session.sid)

    if user_id:
        await audit.log(
            action="auth.logout",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": sid},
            user_id=user_id,
        )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.post("/logout_all")
async def logout_all_user_sessions(
    response: Response,
    sessions: user_session_service_dep,
    audit: user_audit_actor_dep,
):
    user_id = audit.user.id

    await sessions.revoke_all_for_user(user_id)

    await audit.log(
        action="auth.logout_all",
        entity_type="user_session",
        entity_id=None,
        payload={"user_id": user_id},
    )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.get("/sessions", response_model=list[UserSessionOut])
async def get_my_sessions(
    sessions: user_session_service_dep,
    audit: user_audit_actor_dep,
    include_inactive: bool = Query(False),
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    current_sid = await sessions.get_current_sid(refresh_token)

    now = datetime.now(timezone.utc)
    rows = await sessions.repo.list_by_user(audit.user.id, include_inactive=include_inactive)

    result = []
    for session in rows:
        is_active = (session.revoked_at is None) and (session.expires_at > now)
        is_current = current_sid is not None and session.sid == current_sid
        result.append(
            UserSessionOut.model_validate(
                {
                    **session.__dict__,
                    "is_active": is_active,
                    "is_current": is_current,
                }
            )
        )
    return result


@router.delete("/sessions/{sid}", status_code=HTTPStatus.NO_CONTENT)
async def revoke_session(
    sid: str,
    response: Response,
    sessions: user_session_service_dep,
    audit: user_audit_actor_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    current_sid = await sessions.get_current_sid(refresh_token)

    ok = await sessions.revoke_for_user(audit.user.id, sid)
    if not ok:
        raise HTTP404("Session not found")

    await audit.log(
        action="auth.session_revoke",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": sid},
    )

    if current_sid and current_sid == sid:
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
