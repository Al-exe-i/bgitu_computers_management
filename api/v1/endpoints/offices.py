from fastapi import APIRouter, HTTPException
from repositories.office import get_office, update_office, count_faulty_computers
from db.session import session_dep
from dependencies.auth import user_dep
from schemas.office import Office, OfficeUpdate

router = APIRouter()
@router.get("/{office_id}", response_model=Office)
async def get_office_by_id(office_id: int, db: session_dep):
    office = await get_office(db, office_id)
    if office:
        return office
    raise HTTPException(status_code=404, detail="Office not found")


@router.patch("/{office_id}", response_model=Office)
async def update_office_by_id_endpoint(
        db: session_dep, office_id: int,
        office_in: OfficeUpdate,
        user: user_dep
):
    office = await get_office(db, office_id)
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    updated_office = await update_office(db, office_in, office)
    return updated_office


@router.get("/faulty_computers/{office_id}")
async def get_faulty_computers_in_office(db: session_dep, office_id: int):
    count = await count_faulty_computers(db, office_id)
    return {"count": count}