from typing import List
from fastapi import APIRouter, HTTPException

from core.exceptions import HTTP404
from dependencies.additional_hardware import hardware_service_dep
from dependencies.auth import user_dep, technician_dep
from schemas.additional_hardware import AdditionalHardwareRead, AdditionalHardwareCreate, AdditionalHardwareUpdate

router = APIRouter()


@router.post("/", response_model=AdditionalHardwareRead)
async def add_hardware_to_audience(
        data: AdditionalHardwareCreate,
        user: technician_dep,
        service: hardware_service_dep
):
    return await service.create_hardware(data)


@router.get("/{aud_id}", response_model=List[AdditionalHardwareRead])
async def get_audience_hardware(aud_id: int, service: hardware_service_dep):
    return await service.get_hardware_by_audience(aud_id)


@router.patch("/{hardware_id}", response_model=AdditionalHardwareRead)
async def update_hardware_endpoint(
        hardware_id: int,
        hardware_data: AdditionalHardwareUpdate,
        service: hardware_service_dep,
        user: technician_dep
):
    hardware = await service.update_hardware(hardware_id, hardware_data)

    if not hardware:
        raise HTTP404("Hardware not found")

    return hardware


@router.delete("/{hardware_id}")
async def delete_hardware_endpoint(
        hardware_id: int,
        service: hardware_service_dep,
        user: technician_dep
):
    success = await service.delete_hardware(hardware_id)

    if not success:
        raise HTTP404("Hardware not found")

    return {"success": True}


@router.delete("/delete_all/{aud_id}")
async def delete_all_hardware_endpoint(
        aud_id: int,
        service: hardware_service_dep,
        user: user_dep
):
    success = await service.delete_all_hardware(aud_id)

    if not success:
        raise HTTP404("Hardware not found")

    return {"success": True}