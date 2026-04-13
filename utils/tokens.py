import hashlib
from uuid import uuid4

from fastapi.responses import JSONResponse

from core.config import settings
from core.security import generate_access_token


def build_token_response(*, access_token: str, refresh_token: str) -> JSONResponse:
    token_data = {"access_token": access_token, "token_type": "bearer", "status": "success"}
    response = JSONResponse(content=token_data)

    cookie_params = {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "lax",
    }

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **cookie_params,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        **cookie_params,
    )

    return response


def issue_access_token(user_id: int) -> str:
    return generate_access_token(data={"sub": str(user_id)})


def new_refresh_token() -> str:
    return str(uuid4())


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
