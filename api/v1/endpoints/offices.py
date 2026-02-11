from fastapi import APIRouter
from core.exceptions import HTTP404
from dependencies.audit_log import audit_log_service_dep
from dependencies.office import office_service_dep
from dependencies.auth import admin_dep
from dependencies.request_meta import request_meta_dep
from schemas.office import OfficeResponse, OfficeUpdate, OfficeShort, OfficeCreate

router = APIRouter()


@router.get("/", response_model=list[OfficeResponse])
async def get_all_offices(service: office_service_dep):
    offices = await service.get_all()
    return offices


@router.post("/", response_model=OfficeShort)
async def create_office(
        schema: OfficeCreate,
        service: office_service_dep,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep
):
    office = await service.create(schema)

    await audit.log(
        user_id=user.id,
        action="office.create",
        entity_type="office",
        entity_id=office.id,
        payload={"address": office.address},
        **meta,
    )

    return office


@router.delete("/{office_id}", status_code=204)
async def delete_office(
        office_id: int,
        service: office_service_dep,
        user: admin_dep,
        audit: audit_log_service_dep,
        meta: request_meta_dep
):
    await service.delete(office_id)

    await audit.log(
        user_id=user.id,
        action="office.delete",
        entity_type="office",
        entity_id=office_id,
        **meta,
    )


@router.get("/all_short", response_model=list[OfficeShort])
async def get_all_offices_short(service: office_service_dep):
    offices = await service.get_all(full=False)
    return offices


@router.get("/{office_id}", response_model=OfficeResponse)
async def get_office(
        office_id: int,
        service: office_service_dep
):
    office = await service.get(office_id)
    if office:
        return office
    raise HTTP404("Office not found")


@router.patch("/{office_id}", response_model=OfficeResponse)
async def update_office_by_id_endpoint(
        office_id: int,
        office_in: OfficeUpdate,
        service: office_service_dep,
        user: admin_dep
):
    office = await service.get(office_id)

    if not office:
        raise HTTP404("Office not found")

    updated_office = await service.update(office_in, office)
    return updated_office


@router.get("/faulty_computers/{office_id}")
async def get_faulty_computers_in_office(
        office_id: int,
        service: office_service_dep
):
    office = await service.get_short(office_id)

    if not office:
        raise HTTP404("Office not found")

    count = await service.count_faulty(office_id)
    return {"count": count}
