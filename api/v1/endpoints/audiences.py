from fastapi import APIRouter

from api.v1.application_events import dispatch_result_events
from dependencies.events import inventory_event_dispatcher_dep
from dependencies.inventory import inventory_audience_use_cases_dep
from dependencies.audit_actor import admin_audit_actor_dep
from schemas.audience import AudienceCreate, AudienceResponse, AudienceShortResponse, AudienceUpdate

router = APIRouter()


@router.post("", response_model=AudienceShortResponse, status_code=201)
async def create_audience(
    data: AudienceCreate,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    result = await dispatch_result_events(
        await use_cases.create_audience(
            data=data,
            audit=audit,
        ),
        events,
    )

    return result.audience


@router.get("", response_model=list[AudienceResponse])
async def get_audiences(
    use_cases: inventory_audience_use_cases_dep,
):
    return await use_cases.list_audiences()


@router.get("/{audience_id}", response_model=AudienceResponse)
async def get_audience_details(
    audience_id: int,
    use_cases: inventory_audience_use_cases_dep,
):
    return await use_cases.get_audience(audience_id=audience_id)


@router.put("/{audience_id}", response_model=AudienceShortResponse)
async def update_audience(
    audience_id: int,
    data: AudienceUpdate,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    result = await dispatch_result_events(
        await use_cases.update_audience(
            audience_id=audience_id,
            data=data,
            audit=audit,
        ),
        events,
    )

    return result.audience


@router.delete("/{audience_id}", status_code=204)
async def delete_audience(
    audience_id: int,
    use_cases: inventory_audience_use_cases_dep,
    audit: admin_audit_actor_dep,
    events: inventory_event_dispatcher_dep,
):
    await dispatch_result_events(
        await use_cases.delete_audience(
            audience_id=audience_id,
            audit=audit,
        ),
        events,
    )
