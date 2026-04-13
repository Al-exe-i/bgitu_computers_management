from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.exc import IntegrityError

from core.exceptions import HTTP409
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.audiences import audiences_service_dep
from schemas.audience import AudienceCreate, AudienceResponse, AudienceShortResponse, AudienceUpdate
from utils.audit import clean_sensitive
from utils.broadcast import broadcast_audience_updated

router = APIRouter()


@router.post("", response_model=AudienceShortResponse, status_code=201)
async def create_audience(
    data: AudienceCreate,
    service: audiences_service_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
):
    try:
        created = await service.create_audience(data)

        payload = clean_sensitive(data)
        if isinstance(payload, dict) and "hardware" in payload:
            payload["hardware_count"] = len(payload.get("hardware") or [])
            payload.pop("hardware", None)

        await audit.log(
            action="audience.create",
            entity_type="audience",
            entity_id=created.id,
            payload=payload,
        )

        broadcast_audience_updated(background_tasks, created.id)

        return created
    except IntegrityError:
        raise HTTP409("Audience already exists")


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
    return await service.get_one(audience_id)


@router.put("/{audience_id}", response_model=AudienceShortResponse)
async def update_audience(
    audience_id: int,
    data: AudienceUpdate,
    service: audiences_service_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
):
    updated = await service.update_audience(audience_id, data)

    payload = clean_sensitive(data)
    if isinstance(payload, dict) and "hardware" in payload:
        payload["hardware_count"] = len(payload.get("hardware") or [])
        payload.pop("hardware", None)

    await audit.log(
        action="audience.update",
        entity_type="audience",
        entity_id=audience_id,
        payload=payload,
    )

    broadcast_audience_updated(background_tasks, audience_id)
    return updated


@router.delete("/{audience_id}", status_code=204)
async def delete_audience(
    audience_id: int,
    service: audiences_service_dep,
    audit: admin_audit_actor_dep,
    background_tasks: BackgroundTasks,
):
    await service.delete_audience(audience_id)

    await audit.log(
        action="audience.delete",
        entity_type="audience",
        entity_id=audience_id,
        payload=None,
    )

    broadcast_audience_updated(background_tasks, audience_id)
