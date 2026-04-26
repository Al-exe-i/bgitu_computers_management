from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError

from core.exceptions import HTTP400, HTTP404, HTTP409, OfficeNotFoundError
from dependencies.audit_actor import admin_audit_actor_dep
from dependencies.inventory import inventory_office_use_cases_dep
from dependencies.office import office_service_dep
from schemas.office import OfficeCreate, OfficeResponse, OfficeShort, OfficeUpdate

router = APIRouter()


@router.get("", response_model=list[OfficeResponse])
async def get_all_offices(service: office_service_dep):
    return await service.get_all()


@router.post("", response_model=OfficeShort)
async def create_office(
    schema: OfficeCreate,
    use_cases: inventory_office_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    try:
        result = await use_cases.create_office(
            data=schema,
            audit=audit,
        )
    except IntegrityError:
        raise HTTP409("Office already exists")

    return result.office


@router.delete("/{office_id}", status_code=204)
async def delete_office(
    office_id: int,
    use_cases: inventory_office_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    try:
        await use_cases.delete_office(
            office_id=office_id,
            audit=audit,
        )
    except OfficeNotFoundError as exc:
        raise HTTP400(exc.detail)


@router.get("/all_short", response_model=list[OfficeShort])
async def get_all_offices_short(service: office_service_dep):
    return await service.get_all_short()


@router.get("/{office_id}", response_model=OfficeResponse)
async def get_office(
    office_id: int,
    use_cases: inventory_office_use_cases_dep,
):
    try:
        return await use_cases.get_office(office_id=office_id)
    except OfficeNotFoundError as exc:
        raise HTTP404(exc.detail)


@router.patch("/{office_id}", response_model=OfficeShort)
async def update_office_by_id_endpoint(
    office_id: int,
    office_in: OfficeUpdate,
    use_cases: inventory_office_use_cases_dep,
    audit: admin_audit_actor_dep,
):
    try:
        result = await use_cases.update_office(
            office_id=office_id,
            data=office_in,
            audit=audit,
        )
    except OfficeNotFoundError as exc:
        raise HTTP404(exc.detail)

    return result.office
