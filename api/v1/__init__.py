from fastapi import APIRouter
from .endpoints import users, audiences, auth

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audiences.router, prefix="/audiences", tags=["audiences"])
api_router.include_router(auth.router, tags=["auth"])