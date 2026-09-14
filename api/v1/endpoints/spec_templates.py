from typing import Annotated

from fastapi import APIRouter, Query

from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.auth import admin_dep
from dependencies.inventory import inventory_spec_template_use_cases_dep
from modules.inventory.schemas.spec_template import (
    SpecTemplateCreate,
    SpecTemplateResponse,
    SpecTemplateUpdate,
)
from modules.inventory.types import HardwareType

router = APIRouter()


@router.get("", response_model=list[SpecTemplateResponse])
async def list_spec_templates(
    use_cases: inventory_spec_template_use_cases_dep,
    _user: admin_dep,
    hardware_type: Annotated[HardwareType | None, Query()] = None,
):
    return await use_cases.list_templates(hardware_type=hardware_type)


@router.post("", response_model=SpecTemplateResponse, status_code=201)
async def create_spec_template(
    data: SpecTemplateCreate,
    use_cases: inventory_spec_template_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    return await use_cases.create_template(data=data, audit=audit)


@router.patch("/{template_id}", response_model=SpecTemplateResponse)
async def update_spec_template(
    template_id: int,
    data: SpecTemplateUpdate,
    use_cases: inventory_spec_template_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    return await use_cases.update_template(
        template_id=template_id,
        data=data,
        audit=audit,
    )


@router.delete("/{template_id}", status_code=204)
async def delete_spec_template(
    template_id: int,
    use_cases: inventory_spec_template_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    await use_cases.delete_template(template_id=template_id, audit=audit)
