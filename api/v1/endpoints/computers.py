from fastapi import APIRouter
from crud.computer import update_computer
from db.session import session_dep
from dependencies.auth import user_dep
from schemas.computer import Computer, ComputerUpdate

router = APIRouter()


@router.patch("/{computer_id}", response_model=Computer)
async def patch_computer(computer_id: int, schema: ComputerUpdate, db: session_dep, user: user_dep) -> Computer | None:
    computer = await update_computer(db, computer_id, schema)
    return computer
