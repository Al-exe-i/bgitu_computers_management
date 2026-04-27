from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    AudienceGridValidationError,
    AudienceNotFoundError,
    HTTP400,
    HTTP404,
    HTTP409,
)
from dependencies.inventory import inventory_audience_use_cases_dep
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.audiences import audiences_service_dep
from dependencies.realtime import realtime_dep
from schemas.audience import AudienceCreate, AudienceResponse, AudienceShortResponse, AudienceUpdate
from modules.inventory.adapters.fastapi_events import dispatch_inventory_events

router = APIRouter()


@router.post("", response_model=AudienceShortResponse, status_code=201)
async def create_audience(
    data: AudienceCreate,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.create_audience(
            data=data,
            audit=audit,
        )
    except AudienceGridValidationError as exc:
        raise HTTP400(exc.detail)
    except IntegrityError:
        raise HTTP409("Audience already exists")

    dispatch_inventory_events(background_tasks, realtime, result.events)
    return result.audience


@router.get("", response_model=list[AudienceResponse])
async def get_audiences(
    service: audiences_service_dep,
):
    return await service.get_list()


@router.get("/{audience_id}", response_model=AudienceResponse)
async def get_audience_details(
    audience_id: int,
    service: audiences_service_dep,
):
    try:
        return await service.get_one(audience_id)
    except AudienceNotFoundError as exc:
        raise HTTP404(exc.detail)


@router.put("/{audience_id}", response_model=AudienceShortResponse)
async def update_audience(
    audience_id: int,
    data: AudienceUpdate,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.update_audience(
            audience_id=audience_id,
            data=data,
            audit=audit,
        )
    except AudienceNotFoundError as exc:
        raise HTTP404(exc.detail)
    except AudienceGridValidationError as exc:
        raise HTTP400(exc.detail)

    dispatch_inventory_events(background_tasks, realtime, result.events)
    return result.audience


@router.delete("/{audience_id}", status_code=204)
async def delete_audience(
    audience_id: int,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
    realtime: realtime_dep,
):
    try:
        result = await use_cases.delete_audience(
            audience_id=audience_id,
            audit=audit,
        )
    except AudienceNotFoundError as exc:
        raise HTTP404(exc.detail)

    dispatch_inventory_events(background_tasks, realtime, result.events)
