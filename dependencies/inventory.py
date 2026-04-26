from typing import Annotated

from fastapi import Depends

from dependencies.audiences import audiences_service_dep
from dependencies.hardware import hardware_file_service_dep, hardware_service_dep
from dependencies.office import office_service_dep
from modules.inventory.application import (
    InventoryAudienceUseCases,
    InventoryHardwareUseCases,
    InventoryOfficeUseCases,
)


def get_inventory_hardware_use_cases(
    hardware_service: hardware_service_dep,
    hardware_file_service: hardware_file_service_dep,
) -> InventoryHardwareUseCases:
    return InventoryHardwareUseCases(
        hardware_service=hardware_service,
        hardware_file_service=hardware_file_service,
    )


inventory_hardware_use_cases_dep = Annotated[
    InventoryHardwareUseCases,
    Depends(get_inventory_hardware_use_cases),
]


def get_inventory_audience_use_cases(
    audience_service: audiences_service_dep,
) -> InventoryAudienceUseCases:
    return InventoryAudienceUseCases(audience_service)


inventory_audience_use_cases_dep = Annotated[
    InventoryAudienceUseCases,
    Depends(get_inventory_audience_use_cases),
]


def get_inventory_office_use_cases(
    office_service: office_service_dep,
) -> InventoryOfficeUseCases:
    return InventoryOfficeUseCases(office_service)


inventory_office_use_cases_dep = Annotated[
    InventoryOfficeUseCases,
    Depends(get_inventory_office_use_cases),
]
