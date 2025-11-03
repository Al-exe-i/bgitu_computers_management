from fastapi import APIRouter
from .endpoints import users, audiences, auth, additional_hardware, offices, computers

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Пользователи (users)"])
api_router.include_router(audiences.router, prefix="/audiences", tags=["Аудитории (audiences)"])
api_router.include_router(computers.router, prefix='/computers', tags=["Компьютеры (computers)"])
api_router.include_router(auth.router, tags=["Авторизация (auth)"])
api_router.include_router(additional_hardware.router, prefix="/hardware" , tags=["Дополнительное оборудование (additional_hardware)"])
api_router.include_router(offices.router, prefix='/offices', tags=["Корпуса (offices)"])