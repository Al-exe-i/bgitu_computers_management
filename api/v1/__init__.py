from fastapi import APIRouter
from .endpoints import users, audiences, auth, offices

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Пользователи (users)"])
api_router.include_router(audiences.router, prefix="/audiences", tags=["Аудитории (audiences)"])
api_router.include_router(auth.router, tags=["Авторизация (auth)"])
api_router.include_router(offices.router, prefix='/offices', tags=["Корпуса (offices)"])