from starlette.responses import JSONResponse
from core.config import settings
from core.security import create_access_token, create_refresh_token
from models.user import User
from schemas.token import Token


async def create_token_pair_and_build_response(user: User) -> JSONResponse:
    payload = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(data=payload)
    refresh_token = create_refresh_token(data=payload)

    token_data = Token(access_token=access_token, token_type="bearer").model_dump()

    response = JSONResponse(content=token_data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )

    return response