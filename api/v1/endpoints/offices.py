from fastapi import APIRouter, HTTPException

from crud.office import get_office
from db.session import session_dep
from schemas.office import Office

router = APIRouter()
@router.get("/{office_id}", response_model=Office)
async def get_office_by_id_endpoint(office_id: int, db: session_dep):
    office = await get_office(db, office_id)
    if office:
        return office
    raise HTTPException(status_code=404, detail="Office not found")