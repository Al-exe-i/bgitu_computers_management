from typing import List
from fastapi import APIRouter, HTTPException
from starlette import status
from crud.audience import get_all, get_by_id, create_audience, delete_audience
from db.session import session_dep
from schemas.audience import Audience, AudienceCreateRequest

router = APIRouter()


@router.get("/", response_model=List[Audience])
async def get_auditoriums_endpoint(db: session_dep):
    auditoriums = await get_all(db)
    return auditoriums


@router.get("/{aud_id}", response_model=Audience)
async def get_auditorium_by_id_endpoint(db: session_dep, aud_id: int):
    auditorium = await get_by_id(db, aud_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail="Auditorium not found")
    return auditorium


@router.post("/", response_model=Audience, status_code=status.HTTP_201_CREATED)
async def create_audience_endpoint(audience_data: AudienceCreateRequest, db: session_dep):
    """
    Создать новую аудиторию с рядами и компьютерами
    - **id**: номер аудитории
    - **type**: тип аудитории (row 0/perimeter 1)
    - **rows**: список рядов, каждый ряд содержит:
        - **name**: имя ряда в формате "row_XX" (max 10)
        - **computers_count**: количество компьютеров в ряду (1-10)
    """

    try:
        audience = await create_audience(db, audience_data)
        created = await get_by_id(db, audience.id)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create audience: {str(e)}"
        )


@router.delete("/{aud_id}")
async def _delete_audience(db: session_dep, aud_id: int):
    success = await delete_audience(db, aud_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audience not found")
    return {"msg": "Audience deleted"}