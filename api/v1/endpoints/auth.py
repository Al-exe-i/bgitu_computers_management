# api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse
from core.exceptions import HTTP401
from core.security import verify_password
from dependencies.user import user_service_dep
from utils.tokens import create_token_pair_and_build_response

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
        service: user_service_dep,
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await service.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTP401("Invalid credentials")
    return await create_token_pair_and_build_response(user=user)


@router.post("/logout")
async def logout_user():
    response = JSONResponse(content={"message": "Successfully logged out"}, status_code=status.HTTP_200_OK)
    response.delete_cookie(key="refresh_token")
    return response