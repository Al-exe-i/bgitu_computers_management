from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from core.exceptions import HTTP409
from dependencies.audiences import audiences_service_dep
from dependencies.auth import admin_dep
from schemas.audience import AudienceResponse, AudienceCreate, AudienceShortResponse, AudienceUpdate
from utils.broadcast import broadcast_audience_updated

router = APIRouter()

@router.post("", response_model=AudienceShortResponse, status_code=201)
async def create_audience(
        data: AudienceCreate,
        service: audiences_service_dep,
        background_tasks: BackgroundTasks,
        user: admin_dep
):
    """
    Создать аудиторию вместе с сеткой оборудования.
    Принимает JSON с полями аудитории и массивом hardware.
    """
    try:
        created = await service.create_audience(data)
        broadcast_audience_updated(background_tasks, created.id)
        return created
    except IntegrityError:
        raise HTTP409("Такая аудитория уже существует")


@router.get("", response_model=list[AudienceResponse])
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
        background_tasks: BackgroundTasks,
        user: admin_dep
):
    """
    Обновить параметры аудитории и/или перестроить сетку оборудования.
    """
    updated = await service.update_audience(audience_id, data)
    broadcast_audience_updated(background_tasks, audience_id)
    return updated


@router.delete("/{audience_id}", status_code=204)
async def delete_audience(
        audience_id: int,
        service: audiences_service_dep,
        user: admin_dep
):
    """Удалить аудиторию (оборудование удалится каскадно)"""
    await service.delete_audience(audience_id)
