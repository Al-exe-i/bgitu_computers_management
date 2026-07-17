from fastapi import APIRouter, Depends

from dependencies.origin import enforce_trusted_origin

from .endpoints import (
    admin,
    audiences,
    auth,
    hardware,
    hardware_analytics,
    notifications,
    offices,
    spec_templates,
    users,
)

api_router = APIRouter(dependencies=[Depends(enforce_trusted_origin)])
api_router.include_router(admin.router, prefix="/admin", tags=["Администрирование (admin)"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи (users)"])
api_router.include_router(audiences.router, prefix="/audiences", tags=["Аудитории (audiences)"])
api_router.include_router(hardware.router, prefix="/hardware", tags=["Оборудование (hardware)"])
api_router.include_router(auth.router, tags=["Авторизация (auth)"])
api_router.include_router(offices.router, prefix="/offices", tags=["Корпуса (offices)"])
api_router.include_router(
    hardware_analytics.router,
    prefix="/analytics/hardware",
    tags=["Аналитика оборудования (hardware_analytics)"],
)
api_router.include_router(
    spec_templates.router,
    prefix="/spec-templates",
    tags=["Шаблоны характеристик (spec_templates)"],
)
api_router.include_router(notifications.router, tags=["Notifications"])
