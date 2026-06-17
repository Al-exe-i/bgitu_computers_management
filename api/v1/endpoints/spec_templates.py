from fastapi import APIRouter, HTTPException, Query

from dependencies.auth import admin_dep
from dependencies.spec_template import spec_template_service_dep
from models.hardware import HardwareType
from schemas.spec_template import (
    SpecTemplateCreate,
    SpecTemplateResponse,
    SpecTemplateUpdate,
)

router = APIRouter()


@router.get("", response_model=list[SpecTemplateResponse])
async def list_spec_templates(
    service: spec_template_service_dep,
    user: admin_dep,
    hardware_type: HardwareType | None = Query(None),
):
    return await service.list(hardware_type)


@router.post("", response_model=SpecTemplateResponse, status_code=201)
async def create_spec_template(
    data: SpecTemplateCreate,
    service: spec_template_service_dep,
    user: admin_dep,
):
    return await service.create(data)


@router.patch("/{template_id}", response_model=SpecTemplateResponse)
async def update_spec_template(
    template_id: int,
    data: SpecTemplateUpdate,
    service: spec_template_service_dep,
    user: admin_dep,
):
    template = await service.update(template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_spec_template(
    template_id: int,
    service: spec_template_service_dep,
    user: admin_dep,
):
    deleted = await service.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
