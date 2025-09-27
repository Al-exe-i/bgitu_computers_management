# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse
from core.security import verify_password
from db.session import session_dep
from crud.user import get_user_by_email
from dependencies.auth import get_current_user
from models.user import User
from utils.tokens import create_token_pair_and_build_response

router = APIRouter()


@router.post("/token")
async def login_for_access_token(
        db: session_dep,
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_token_pair_and_build_response(user=user)


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    response = JSONResponse(content={"message": "Successfully logged out"}, status_code=status.HTTP_200_OK)
    response.delete_cookie(key="refresh_token")
    return response