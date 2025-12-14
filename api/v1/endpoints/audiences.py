from typing import List
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status
from core.exceptions import HTTP404
from dependencies.audiences import audiences_service_dep
from dependencies.auth import technician_dep
from schemas.audience import AudienceUpdate, AudienceResponse, AudienceCreate
from loguru import logger

router = APIRouter()

@router.post("/audiences", response_model=AudienceResponse, status_code=status.HTTP_201_CREATED)
async def create_audience(
    data: AudienceCreate,
    service: audiences_service_dep
):
    """
    Создать аудиторию вместе с сеткой оборудования.
    Принимает JSON с полями аудитории и массивом hardware.
    """
    return await service.create_audience(data)


@router.get("/audiences", response_model=List[AudienceResponse])
async def get_audiences(
    service: audiences_service_dep
):
    """Получить список всех аудиторий"""
    return await service.get_list()


@router.get("/audiences/{audience_id}", response_model=AudienceResponse)
async def get_audience_details(
    audience_id: int,
    service: audiences_service_dep
):
    """Получить детальную информацию об аудитории и оборудовании внутри"""
    return await service.get_one(audience_id)


@router.delete("/audiences/{audience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audience(
    audience_id: int,
    service: audiences_service_dep
):
    """Удалить аудиторию (оборудование удалится каскадно)"""
    await service.delete_audience(audience_id)
