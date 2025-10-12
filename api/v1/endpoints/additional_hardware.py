from typing import List
from fastapi import APIRouter, HTTPException
from crud.additional_hardware import create_hardware, get_hardware_by_audience, update_hardware, delete_hardware, \
    delete_all_hardware
from db.session import session_dep
from dependencies.auth import user_dep
from schemas.additional_hardware import AdditionalHardware, AdditionalHardwareCreate, AdditionalHardwareUpdate

router = APIRouter()


@router.post("/{aud_id}", response_model=AdditionalHardware)
async def add_hardware_to_audience(
        aud_id: int,
        hardware_data: AdditionalHardwareCreate,
        db: session_dep,
        user: user_dep
):
    hardware_data.audience_id = aud_id

    hardware = await create_hardware(db, hardware_data)
    return hardware


@router.get("/{aud_id}", response_model=List[AdditionalHardware])
async def get_audience_hardware(aud_id: int, db: session_dep):
    hardware_list = await get_hardware_by_audience(db, aud_id)
    return hardware_list


@router.patch("/{hardware_id}", response_model=AdditionalHardware)
async def update_hardware_endpoint(
        hardware_id: int,
        hardware_data: AdditionalHardwareUpdate,
        db: session_dep,
        user: user_dep
):
    hardware = await update_hardware(db, hardware_id, hardware_data)

    if not hardware:
        raise HTTPException(status_code=404, detail="Hardware not found")

    return hardware


@router.delete("/{hardware_id}")
async def delete_hardware_endpoint(
        hardware_id: int,
        db: session_dep,
        user: user_dep
):
    success = await delete_hardware(db, hardware_id)

    if not success:
        raise HTTPException(status_code=404, detail="Hardware not found")

    return {"success": True}


@router.delete("/delete_all/{aud_id}")
async def delete_all_hardware_endpoint(
        aud_id: int,
        db: session_dep,
        user: user_dep
):
    success = await delete_all_hardware(db, aud_id)

    if not success:
        raise HTTPException(status_code=404, detail="Hardware not found")

    return {"success": True}