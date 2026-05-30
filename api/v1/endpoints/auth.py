from http import HTTPStatus

from fastapi import APIRouter, Cookie, Depends, Query
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from api.v1.application_events import dispatch_result_events
from dependencies.audit_actor import audit_ctx_dep, user_audit_actor_dep
from dependencies.events import identity_event_dispatcher_dep
from dependencies.identity import identity_auth_use_cases_dep
from schemas.invite import (
    InvitePreviewRequest,
    InvitePreviewResponse,
    RegisterByInviteRequest,
    RegisterByInviteResponse,
)
from schemas.user_session import UserSessionOut
from utils.tokens import build_token_response

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
    use_cases: identity_auth_use_cases_dep,
    events: identity_event_dispatcher_dep,
    audit: audit_ctx_dep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    result = await dispatch_result_events(
        await use_cases.login(
            email=form_data.username,
            password=form_data.password,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
            audit=audit,
        ),
        events,
    )

    return build_token_response(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
    )


@router.post("/refresh")
async def refresh_tokens(
    use_cases: identity_auth_use_cases_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    result = await use_cases.refresh(
        refresh_token=refresh_token,
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
        audit=audit,
    )

    return build_token_response(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
    )


@router.post("/logout")
async def logout_user(
    response: Response,
    use_cases: identity_auth_use_cases_dep,
    audit: audit_ctx_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    await use_cases.logout(
        refresh_token=refresh_token,
        ip=audit.meta.get("ip"),
        user_agent=audit.meta.get("user_agent"),
        audit=audit,
    )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.post("/logout_all")
async def logout_all_user_sessions(
    response: Response,
    use_cases: identity_auth_use_cases_dep,
    events: identity_event_dispatcher_dep,
    audit: user_audit_actor_dep,
):
    user_id = audit.user.id

    result = await dispatch_result_events(
        await use_cases.logout_all(
            user_id=user_id,
            ip=audit.meta.get("ip"),
            user_agent=audit.meta.get("user_agent"),
            audit=audit,
        ),
        events,
    )

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {"message": "Successfully logged out"}


@router.get("/sessions", response_model=list[UserSessionOut])
async def get_my_sessions(
    use_cases: identity_auth_use_cases_dep,
    audit: user_audit_actor_dep,
    include_inactive: bool = Query(False),
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    return await use_cases.list_user_sessions(
        user_id=audit.user.id,
        include_inactive=include_inactive,
        refresh_token=refresh_token,
    )


@router.delete("/sessions/{sid}", status_code=HTTPStatus.NO_CONTENT)
async def revoke_session(
    sid: str,
    response: Response,
    use_cases: identity_auth_use_cases_dep,
    audit: user_audit_actor_dep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    result = await use_cases.revoke_session(
        user_id=audit.user.id,
        sid=sid,
        refresh_token=refresh_token,
        audit=audit,
    )

    if result.session.revoked_current_session:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")


@router.post("/auth/invite/preview", response_model=InvitePreviewResponse)
async def preview_invite(
    data: InvitePreviewRequest,
    use_cases: identity_auth_use_cases_dep,
):
    return await use_cases.preview_invite(token=data.token)


@router.post("/auth/invite/register", response_model=RegisterByInviteResponse)
async def register_by_invite(
    data: RegisterByInviteRequest,
    use_cases: identity_auth_use_cases_dep,
    audit: audit_ctx_dep,
):
    result = await use_cases.register_by_invite(
        data=data,
        audit=audit,
    )

    return result.registration
