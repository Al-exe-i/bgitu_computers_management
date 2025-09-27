from typing import List
from fastapi import APIRouter, HTTPException
from crud.auditorium import get_all, get_by_id
from db.session import session_dep
from schemas.auditorium import Auditorium

router = APIRouter()


@router.get("/auditoriums", response_model=List[Auditorium])
async def get_auditoriums(db: session_dep):
    auditoriums = await get_all(db)
    return auditoriums


@router.get("/auditoriums/{aud_id}", response_model=Auditorium)
async def get_auditorium_by_id(db: session_dep, aud_id: int):
    auditorium = await get_by_id(db, aud_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail="Auditorium not found")
    return auditorium