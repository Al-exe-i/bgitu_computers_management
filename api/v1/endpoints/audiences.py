from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status
from crud.audience import get_all, get_by_id, create_audience, delete_audience, update_audience
from db.session import session_dep
from dependencies.auth import user_dep
from schemas.audience import Audience, AudienceCreateRequest, AudienceUpdate

router = APIRouter()


@router.get("/", response_model=List[Audience])
async def get_auditoriums_endpoint(db: session_dep):
    """
    Получить все аудитории
    """
    auditoriums = await get_all(db)
    return auditoriums


@router.get("/{aud_id}", response_model=Audience)
async def get_auditorium_by_id_endpoint(db: session_dep, aud_id: int):
    """
    Получить аудиторию по её номеру
    """
    auditorium = await get_by_id(db, aud_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail="Auditorium not found")
    return auditorium


@router.post("/", response_model=Audience, status_code=status.HTTP_201_CREATED)
async def create_audience_endpoint(audience_data: AudienceCreateRequest, db: session_dep, user: user_dep):
    """
    Создать новую аудиторию с рядами и компьютерами
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
        await create_audience(db, audience_data)
        created = await get_by_id(db, audience_data.id)
        return created
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e.statement))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create audience: {str(e)}"
        )


@router.patch("/update/{aud_id}", response_model=Audience, response_model_exclude={"rows", "additional_hardware"})
async def update_audience_endpoint(aud_id: int, audience_data: AudienceUpdate, db: session_dep, user: user_dep):
    """
     Обновляет некоторые параметры аудитории. Параметры описаны моделью
    """
    updated = await update_audience(db, aud_id, audience_data)
    return updated


@router.delete("/{aud_id}")
async def delete_audience_endpoint(db: session_dep, aud_id: int, user: user_dep):
    """
    Удаляет аудиторию и все её ряды и компьютеры каскадно
    """
    success = await delete_audience(db, aud_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audience not found")
    return {"msg": "Audience deleted"}
