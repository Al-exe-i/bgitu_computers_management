from fastapi import APIRouter
from .endpoints import users, audiences, auth, offices, hardware, admin, hardware_analytics

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["Администрирование (admin)"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи (users)"])
api_router.include_router(audiences.router, prefix="/audiences", tags=["Аудитории (audiences)"])
api_router.include_router(hardware.router, prefix="/hardware", tags=["Оборудование (hardware)"])
api_router.include_router(auth.router, tags=["Авторизация (auth)"])
api_router.include_router(offices.router, prefix='/offices', tags=["Корпуса (offices)"])
api_router.include_router(hardware_analytics.router, prefix="/analytics/hardware", tags=["Аналитика оборудования (hardware_analytics)"])