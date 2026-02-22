# api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse
from core.exceptions import HTTP401
from core.security import verify_password, verify_token
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import user_dep
from dependencies.request_meta import request_meta_dep
from dependencies.user import user_service_dep
from dependencies.user_session_service import user_session_service_dep
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
async def refresh_access_token(
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
        # reuse detection: старый refresh пытаются использовать повторно
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
    response.delete_cookie(key="refresh_token", path="/api/v1/")
    return response


@router.post("/logout_all")
async def logout_all_user(
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
    response.delete_cookie(key="refresh_token", path="/api/v1/")
    return response