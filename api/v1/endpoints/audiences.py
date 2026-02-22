from fastapi import APIRouter, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from core.exceptions import HTTP409
from dependencies.audiences import audiences_service_dep
from dependencies.audit_log import audit_log_service_dep
from dependencies.auth import admin_dep
from dependencies.request_meta import request_meta_dep
from schemas.audience import AudienceResponse, AudienceCreate, AudienceShortResponse, AudienceUpdate
from utils.audit import clean_sensitive
from utils.broadcast import broadcast_audience_updated

router = APIRouter()

@router.post("", response_model=AudienceShortResponse, status_code=201)
async def create_audience(
        data: AudienceCreate,
        service: audiences_service_dep,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        background_tasks: BackgroundTasks,
):
    try:
        created = await service.create_audience(data)

        payload = clean_sensitive(data)
        if isinstance(payload, dict) and "hardware" in payload:
            payload["hardware_count"] = len(payload.get("hardware") or [])
            payload.pop("hardware", None)

        await audit.log(
            user_id=user.id,
            action="audience.create",
            entity_type="audience",
            entity_id=created.id,
            payload=payload,
            **meta,
        )

        broadcast_audience_updated(background_tasks, created.id)
        return created

    except IntegrityError:
        raise HTTP409("Audience already exists")


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
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        background_tasks: BackgroundTasks,
):
    updated = await service.update_audience(audience_id, data)

    payload = clean_sensitive(data)
    if isinstance(payload, dict) and "hardware" in payload:
        payload["hardware_count"] = len(payload.get("hardware") or [])
        payload.pop("hardware", None)

    await audit.log(
        user_id=user.id,
        action="audience.update",
        entity_type="audience",
        entity_id=audience_id,
        payload=payload,
        **meta,
    )

    broadcast_audience_updated(background_tasks, audience_id)
    return updated


@router.delete("/{audience_id}", status_code=204)
async def delete_audience(
        audience_id: int,
        service: audiences_service_dep,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep,
        background_tasks: BackgroundTasks,
):
    await service.delete_audience(audience_id)

    await audit.log(
        user_id=user.id,
        action="audience.delete",
        entity_type="audience",
        entity_id=audience_id,
        payload=None,
        **meta,
    )

    broadcast_audience_updated(background_tasks, audience_id)
