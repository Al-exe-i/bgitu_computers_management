from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.endpoints.offices import router
from core.exception_handlers import register_exception_handlers
from core.exceptions.floor_plan import FloorPlanConflictError
from dependencies.audit_log import get_audit_log_service
from dependencies.auth import get_current_user
from dependencies.floor_plans import get_floor_plan_use_cases
from dependencies.user import get_user_service
from modules.identity.public import UserRole
from modules.inventory.schemas.floor_plan import FloorInfo, FloorPlanResponse


@pytest.fixture
def api():
    app = FastAPI()
    app.include_router(router, prefix="/offices")
    register_exception_handlers(app)
    response = FloorPlanResponse(
        office_id=1, floor=2, width=20, height=12, revision=0, rooms=[]
    )
    use_cases = SimpleNamespace(
        get=AsyncMock(return_value=response),
        update=AsyncMock(return_value=response),
        get_info=AsyncMock(return_value=FloorInfo()),
        update_info=AsyncMock(return_value=FloorInfo(name="Лаборатории")),
    )
    app.dependency_overrides[get_floor_plan_use_cases] = lambda: use_cases
    app.dependency_overrides[get_audit_log_service] = lambda: SimpleNamespace(
        log=AsyncMock()
    )
    app.dependency_overrides[get_user_service] = lambda: SimpleNamespace(
        get_for_authentication=AsyncMock(return_value=None)
    )
    return app, use_cases


def test_floor_plan_is_public(api):
    app, _ = api
    with TestClient(app) as client:
        response = client.get("/offices/1/floors/2/plan")
    assert response.status_code == 200 and response.json()["revision"] == 0


def test_floor_info_is_public(api):
    app, _ = api
    with TestClient(app) as client:
        response = client.get("/offices/1/floors/2/info")
    assert response.status_code == 200
    assert response.json() == {"name": None, "description": None}


@pytest.mark.parametrize(
    "role, status", [(None, 401), (UserRole.teacher, 403), (UserRole.admin, 200)]
)
def test_floor_info_write_permissions(api, role, status):
    app, use_cases = api
    if role is not None:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=7, role=role, is_superuser=False
        )
    with TestClient(app) as client:
        response = client.patch(
            "/offices/1/floors/2/info", json={"name": "Лаборатории"}
        )
    assert response.status_code == status
    assert use_cases.update_info.await_count == (1 if status == 200 else 0)


def test_guest_cannot_save_floor_plan(api):
    app, use_cases = api
    with TestClient(app) as client:
        response = client.put(
            "/offices/1/floors/2/plan",
            json={"width": 20, "height": 12, "revision": 0, "rooms": []},
        )
    assert response.status_code == 401
    use_cases.update.assert_not_awaited()


@pytest.mark.parametrize(
    "role, superuser, status",
    [
        (UserRole.teacher, False, 403),
        (UserRole.admin, False, 200),
        (UserRole.admin, True, 200),
    ],
)
def test_only_admin_can_save(api, role, superuser, status):
    app, use_cases = api
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7, role=role, is_superuser=superuser
    )
    with TestClient(app) as client:
        response = client.put(
            "/offices/1/floors/2/plan",
            json={"width": 20, "height": 12, "revision": 0, "rooms": []},
        )
    assert response.status_code == status
    if status == 403:
        use_cases.update.assert_not_awaited()


def test_conflicting_revision_returns_409(api):
    app, use_cases = api
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=7, role=UserRole.admin, is_superuser=False
    )
    use_cases.update.side_effect = FloorPlanConflictError()
    with TestClient(app) as client:
        response = client.put(
            "/offices/1/floors/2/plan",
            json={"width": 20, "height": 12, "revision": 0, "rooms": []},
        )
    assert response.status_code == 409
