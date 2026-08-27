from typing import Annotated

from fastapi import Depends

from dependencies.analytics import analytics_service_dep
from dependencies.audiences import audiences_service_dep
from dependencies.hardware import (
    hardware_file_service_dep,
    hardware_file_streaming_service_dep,
    hardware_service_dep,
)
from dependencies.office import office_service_dep
from dependencies.spec_template import spec_template_service_dep
from modules.inventory.application import (
    InventoryAnalyticsQueries,
    InventoryAudienceUseCases,
    InventoryHardwareFileQueries,
    InventoryHardwareUseCases,
    InventoryOfficeUseCases,
    InventorySpecTemplateUseCases,
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


def get_inventory_hardware_file_queries(
    service: hardware_file_streaming_service_dep,
) -> InventoryHardwareFileQueries:
    return InventoryHardwareFileQueries(service)


inventory_hardware_file_queries_dep = Annotated[
    InventoryHardwareFileQueries,
    Depends(get_inventory_hardware_file_queries),
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


def get_inventory_spec_template_use_cases(
    service: spec_template_service_dep,
) -> InventorySpecTemplateUseCases:
    return InventorySpecTemplateUseCases(service)


inventory_spec_template_use_cases_dep = Annotated[
    InventorySpecTemplateUseCases,
    Depends(get_inventory_spec_template_use_cases),
]


def get_inventory_analytics_queries(
    service: analytics_service_dep,
) -> InventoryAnalyticsQueries:
    return InventoryAnalyticsQueries(service)


inventory_analytics_queries_dep = Annotated[
    InventoryAnalyticsQueries,
    Depends(get_inventory_analytics_queries),
]
