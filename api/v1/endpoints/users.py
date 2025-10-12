# api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.responses import StreamingResponse
import mimetypes
from core.config import settings
from db.session import session_dep
from models.user import User
from schemas.token import Token
from schemas.user import UserCreate, UserOut, UserUpdate
from crud.user import get_user_by_email, create_user, get_user, delete_user, update_user
from dependencies.auth import get_current_refresh_user, superuser_dep, user_dep
from utils.tokens import create_token_pair_and_build_response
import os

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def _create_user(
        db: session_dep,
        user_in: UserCreate,
        current_user: superuser_dep
):
    existing_user = await get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, schema=user_in)
    return user


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: user_dep):
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def read_user(db: session_dep, user_id: int, current_user: user_dep):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Can't get this user")
    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/photo")
async def get_user_photo(db: session_dep, user: user_dep):
    if not user.photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found for this user"
        )

    file_path = os.path.join(settings.static.upload_dir, user.photo)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo file not found on server"
        )

    media_type, _ = mimetypes.guess_type(file_path)
    if media_type is None:
        media_type = "image/*"

    def file_iterator(path):
        with open(path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(file_iterator(file_path), media_type=media_type)


@router.delete("/{user_id}")
async def _delete_user(db: session_dep, user_id: int,
                      current_user: superuser_dep
                      ):
    user = await delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserOut)
async def _update_user(
        db: session_dep,
        user_id: int,
        user_in: UserUpdate,
        current_user: user_dep
):
    # Разрешить редактировать только себя, если не SU
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this user")

    user = await get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user = await update_user(db, orm_model=user, schema=user_in)
    return updated_user


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        current_user: User = Depends(get_current_refresh_user),
        refresh_token: str | None = Cookie(None, alias="refresh_token"),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")
    return await create_token_pair_and_build_response(user=current_user)
