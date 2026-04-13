# api/v1/endpoints/auth.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Cookie, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from core.exceptions import HTTP401, HTTP404
from core.security import verify_password, verify_token
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import user_dep
from dependencies.invite import invite_service_dep
from dependencies.request_meta import request_meta_dep
from dependencies.user import user_service_dep
from dependencies.user_session_service import user_session_service_dep
from schemas.invite import InvitePreviewResponse, InvitePreviewRequest, RegisterByInviteResponse, \
    RegisterByInviteRequest
from schemas.user_session import UserSessionOut
from utils.tokens import issue_access_token, issue_refresh_token, build_token_response

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
        service: user_service_dep,
        sessions: user_session_service_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await service.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTP401("Invalid credentials")

    # создаём новую “сессию устройства”
    sid = sessions.new_sid()
    jti = sessions.new_jti()

    await sessions.create_session(
        user_id=user.id,
        sid=sid,
        refresh_jti=jti,
        ip=meta.get("ip"),
        user_agent=meta.get("user_agent"),
    )

    access = issue_access_token(user.id)
    refresh = issue_refresh_token(user.id, sid, jti)

    await audit.log(
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=user.id,
        payload={"email": user.email, "sid": sid},
        **meta,
    )

    return build_token_response(access_token=access, refresh_token=refresh)


@router.post("/refresh")
async def refresh_tokens(
        service: user_service_dep,
        sessions: user_session_service_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    if not refresh_token:
        raise HTTP401("No refresh token provided")

    payload = verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTP401("Couldn't validate refresh token")

    sub = payload.get("sub")
    sid = payload.get("sid")
    old_jti = payload.get("jti")

    if not sub or not sid or not old_jti:
        raise HTTP401("Invalid refresh token")

    user = await service.get(int(sub))
    if not user:
        raise HTTP401("User not found")

    new_jti = sessions.new_jti()

    rotated = await sessions.rotate(sid=sid, old_jti=old_jti, new_jti=new_jti)
    if not rotated:
        # это reuse: старый refresh пытаются использовать повторно, отзываем
        await sessions.revoke(sid)

        await audit.log(
            user_id=user.id,
            action="auth.refresh_reuse",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": sid},
            **meta,
        )
        raise HTTP401("Refresh token revoked")

    access = issue_access_token(user.id)
    refresh = issue_refresh_token(user.id, sid, new_jti)

    await audit.log(
        user_id=user.id,
        action="auth.refresh",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": sid},
        **meta,
    )

    return build_token_response(access_token=access, refresh_token=refresh)


@router.post("/logout")
async def logout_user(
        sessions: user_session_service_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    sid = None
    user_id = None

    if refresh_token:
        payload = verify_token(refresh_token, "refresh")
        if payload:
            sid = payload.get("sid")
            sub = payload.get("sub")
            if sid:
                await sessions.revoke(sid)
            if sub:
                user_id = int(sub)

    if user_id:
        await audit.log(
            user_id=user_id,
            action="auth.logout",
            entity_type="user_session",
            entity_id=None,
            payload={"sid": sid},
            **meta,
        )

    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return response


@router.post("/logout_all")
async def logout_all_user_sessions(
        sessions: user_session_service_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        user: user_dep,
):
    user_id = user.id

    await sessions.revoke_all_for_user(user_id)

    await audit.log(
        user_id=user_id,
        action="auth.logout_all",
        entity_type="user_session",
        entity_id=None,
        payload={"user_id": user_id},
        **meta,
    )

    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return response


@router.get("/sessions", response_model=list[UserSessionOut])
async def get_my_sessions(
    sessions: user_session_service_dep,
    user: user_dep,
    include_inactive: bool = Query(False),
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    # current sid, чтобы подсветить текущую сессию
    current_sid = None
    if refresh_token:
        payload = verify_token(refresh_token, "refresh")
        if payload:
            current_sid = payload.get("sid")

    now = datetime.now(timezone.utc)
    rows = await sessions.repo.list_by_user(user.id, include_inactive=include_inactive)

    result = []
    for s in rows:
        is_active = (s.revoked_at is None) and (s.expires_at > now)
        is_current = (current_sid is not None and s.sid == current_sid)
        result.append(UserSessionOut.model_validate(
            {**s.__dict__, "is_active": is_active, "is_current": is_current}
        ))
    return result


@router.delete("/sessions/{sid}")
async def revoke_session(
    sid: str,
    sessions: user_session_service_dep,
    user: user_dep,
    audit: audit_log_service_dep,
    meta: request_meta_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    ok = await sessions.revoke_for_user(user.id, sid)
    if not ok:
        raise HTTP404("Session not found")

    await audit.log(
        user_id=user.id,
        action="auth.session_revoke",
        entity_type="user_session",
        entity_id=None,
        payload={"sid": sid},
        **meta,
    )

    current_sid = None
    if refresh_token:
        payload = verify_token(refresh_token, "refresh")
        if payload:
            current_sid = payload.get("sid")

    response = JSONResponse({"status": "success"})
    if current_sid and current_sid == sid:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
    return response


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
):
    result = await service.register_by_invite(
        data,
        get_user_by_email=user_service.get_by_email,
        create_user=user_service.create,
    )

    return result