from datetime import timedelta
from starlette.responses import JSONResponse
from core.config import settings
from core.security import create_access_token, create_refresh_token
from models.user import User
from schemas.token import Token


async def create_token_pair_and_build_response(user: User) -> JSONResponse:
    access_token_expires = timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": user.email}, expires_delta=refresh_token_expires)

    token_data = Token(access_token=access_token, token_type="bearer").model_dump()

    response = JSONResponse(content=token_data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/"
    )

    return response