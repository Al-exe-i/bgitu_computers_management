from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError

from core.exceptions import HTTP400, HTTP404, HTTP409
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.office import office_service_dep
from schemas.office import OfficeCreate, OfficeResponse, OfficeShort, OfficeUpdate
from utils.audit import changed_fields

router = APIRouter()


@router.get("", response_model=list[OfficeResponse])
async def get_all_offices(service: office_service_dep):
    return await service.get_all()


@router.post("", response_model=OfficeShort)
async def create_office(
    schema: OfficeCreate,
    service: office_service_dep,
    audit: admin_audit_actor_dep,
):
    try:
        office = await service.create(schema)

        await audit.log(
            action="office.create",
            entity_type="office",
            entity_id=office.id,
            payload={"address": office.address},
        )
    except IntegrityError:
        raise HTTP409("Office already exists")

    return office


@router.delete("/{office_id}", status_code=204)
async def delete_office(
    office_id: int,
    service: office_service_dep,
    audit: admin_audit_actor_dep,
):
    result = await service.delete(office_id)
    if not result:
        raise HTTP400("Office not found")

    await audit.log(
        action="office.delete",
        entity_type="office",
        entity_id=office_id,
    )


@router.get("/all_short", response_model=list[OfficeShort])
async def get_all_offices_short(service: office_service_dep):
    return await service.get_all(full=False)


@router.get("/{office_id}", response_model=OfficeResponse)
async def get_office(
    office_id: int,
    service: office_service_dep,
):
    office = await service.get(office_id)
    if office:
        return office
    raise HTTP404("Office not found")


@router.patch("/{office_id}", response_model=OfficeShort)
async def update_office_by_id_endpoint(
    office_id: int,
    office_in: OfficeUpdate,
    service: office_service_dep,
    audit: admin_audit_actor_dep,
):
    office = await service.get_short(office_id)
    if not office:
        raise HTTP404("Office not found")

    updated_office = await service.update(office_in, office)

    await audit.log(
        action="office.update",
        entity_type="office",
        entity_id=office_id,
        payload={
            "office_id": office_id,
            "changed_fields": changed_fields(office_in),
        },
    )

    return updated_office


@router.get("/faulty_computers/{office_id}")
async def get_faulty_computers_in_office(
    office_id: int,
    service: office_service_dep,
):
    office = await service.get_short(office_id)

    if not office:
        raise HTTP404("Office not found")

    count = await service.count_faulty(office_id)
    return {"count": count}
