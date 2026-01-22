from fastapi import APIRouter
from starlette import status
from dependencies.audiences import audiences_service_dep
from dependencies.auth import admin_dep
from schemas.audience import AudienceResponse, AudienceCreate, AudienceShortResponse, AudienceUpdate

router = APIRouter()

@router.post("/", response_model=AudienceShortResponse, status_code=status.HTTP_201_CREATED)
async def create_audience(
        data: AudienceCreate,
        service: audiences_service_dep,
        user: admin_dep
):
    """
    Создать аудиторию вместе с сеткой оборудования.
    Принимает JSON с полями аудитории и массивом hardware.
    """
    return await service.create_audience(data)


@router.get("/", response_model=list[AudienceResponse])
async def get_audiences(
    service: audiences_service_dep
):
    """Получить список всех аудиторий"""
    return await service.get_list()


@router.get("/{audience_id}", response_model=AudienceResponse)
async def get_audience_details(
    audience_id: int,
    service: audiences_service_dep
):
    """Получить детальную информацию об аудитории и оборудовании внутри"""
    return await service.get_one(audience_id)


@router.put("/{audience_id}", response_model=AudienceShortResponse)
async def update_audience(
        audience_id: int,
        data: AudienceUpdate,
        service: audiences_service_dep,
        user: admin_dep
):
    """
    Обновить параметры аудитории и/или перестроить сетку оборудования.
    """
    return await service.update_audience(audience_id, data)


@router.delete("/{audience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audience(
        audience_id: int,
        service: audiences_service_dep,
        user: admin_dep
):
    """Удалить аудиторию (оборудование удалится каскадно)"""
    await service.delete_audience(audience_id)
