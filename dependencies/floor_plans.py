from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from modules.inventory.application.floor_plans import InventoryFloorPlanUseCases
from modules.inventory.repositories.floor_plans import FloorPlanRepository
from modules.inventory.services.floor_plans import FloorPlanService


def get_floor_plan_use_cases(session: session_dep) -> InventoryFloorPlanUseCases:
    return InventoryFloorPlanUseCases(FloorPlanService(FloorPlanRepository(session)))


floor_plan_use_cases_dep = Annotated[
    InventoryFloorPlanUseCases, Depends(get_floor_plan_use_cases)
]
