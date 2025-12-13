from starlette.responses import JSONResponse
from core.config import settings
from core.security import generate_token
from models import User
from schemas.token import Token
from schemas.user import UserOut


async def create_token_pair_and_build_response(user: User | UserOut) -> JSONResponse:
    payload = {"sub": str(user.id)}
    access_token = generate_token(data=payload, token_type="access")
    refresh_token = generate_token(data=payload, token_type="refresh")

    token_data = Token(access_token=access_token, token_type="bearer").model_dump()

    response = JSONResponse(content=token_data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/users/refresh"
    )

    return response