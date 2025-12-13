from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status
from core.exceptions import HTTP404
from dependencies.audiences import audiences_service_dep
from dependencies.auth import technician_dep
from schemas.audience import AudienceRead, AudienceCreateRequest, AudienceUpdate
from loguru import logger

router = APIRouter()


@router.get("/", response_model=List[AudienceRead])
async def get_auditoriums(service: audiences_service_dep):
    """
    Получить все аудитории
    """
    return await service.get_all()


@router.get("/{aud_id}", response_model=AudienceRead)
async def get_auditorium_by_id(
        aud_id: int,
        service: audiences_service_dep
):
    """
    Получить аудиторию по её номеру
    """
    result = await service.get(aud_id)
    if not result:
        raise HTTP404("Audience not found")
    return result


@router.get("/get_available_for_creation/")
async def get_available_for_creation(
        service: audiences_service_dep,
        user: technician_dep
):
    return await service.get_available_for_creation()


@router.post("/", response_model=AudienceRead, status_code=status.HTTP_201_CREATED)
async def create_audience(
        audience_data: AudienceCreateRequest,
        service: audiences_service_dep,
        user: technician_dep
):
    """
    Создать новую аудиторию с рядами и компьютерами
    Вы должны иметь права не менее специалиста ОИ
    - **id**: номер аудитории
    - **type**: тип аудитории (row 0/perimeter 1)
    - **rows**: список рядов, каждый ряд содержит:
        - **name**: имя ряда в формате "row_XX" (max 10)
        - **computers_count**: количество компьютеров в ряду (1-10)
        - **broken_ids**: id неисправных компьютеров в данном ряду, итерация идёт с 1.
        Если сломан первый, третий и пятый, то так и пишите [1, 3, 5].
        Если сломанных нет, то оставьте список пустым
    - **office_id**: Номер корпуса (1 или 2)
    """
    try:
        created = await service.create(audience_data)
        return created
    except IntegrityError as e:
        logger.error(f"Can't create audience: {e}")
        raise HTTPException(status_code=409, detail="Audience already exists")
    except Exception as e:
        logger.error(f"Can't create audience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audience"
        )


@router.patch("/update/{aud_id}", response_model=AudienceRead, response_model_exclude={"rows", "additional_hardware"})
async def update_audience(
        aud_id: int,
        audience_data: AudienceUpdate,
        service: audiences_service_dep,
        user: technician_dep
):
    """
     Обновляет некоторые параметры аудитории. Параметры описаны моделью.
     Вы должны иметь права не менее специалиста ОИ.
    """
    updated = await service.update(aud_id, audience_data)
    if not updated:
        raise HTTP404("Audience not found")
    return updated


@router.delete("/{aud_id}")
async def delete_audience(
        aud_id: int,
        service: audiences_service_dep,
        user: technician_dep
):
    """
    Удаляет аудиторию и все её ряды и компьютеры каскадно
    """
    success = await service.delete(aud_id)
    if not success:
        raise HTTP404("Audience not found")
    return {"msg": "Audience deleted"}
