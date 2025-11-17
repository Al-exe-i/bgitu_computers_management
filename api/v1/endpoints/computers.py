from fastapi import APIRouter, HTTPException
from dependencies.auth import user_dep
from dependencies.computer import computer_service_dep
from schemas.computer import ComputerRead, ComputerUpdate
from websocket.routes import manager

router = APIRouter()


@router.patch("/{computer_id}", response_model=ComputerRead)
async def patch_computer(computer_id: int, schema: ComputerUpdate, service: computer_service_dep, user: user_dep) -> ComputerRead | None:
    computer = await service.update(computer_id, schema)
    if computer is None:
        raise HTTPException(status_code=404, detail="Computer not found")

    await manager.broadcast({"audience_updated": schema.audience_id})
    return computer
