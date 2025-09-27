from fastapi import APIRouter
from .endpoints import users, auth, auditoriums

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auditoriums.router, prefix="/auditoriums", tags=["auditoriums"])
api_router.include_router(auth.router, tags=["auth"])