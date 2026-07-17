from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from dependencies.audit_log import get_audit_log_service
from dependencies.events import get_inventory_event_dispatcher
from dependencies.inventory import get_inventory_hardware_use_cases
from dependencies.user import get_user_service
from main import app
from models.user import UserRole
from schemas.user import UserOut
from utils.tokens import issue_access_token


def make_user(*, user_id: int, role: UserRole) -> UserOut:
    return UserOut(
        id=user_id,
        email=f"user{user_id}@example.ru",
        name="Alex",
        surname="Ivanov",
        photo=None,
        role=role,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=False,
    )


class DummyUserService:
    def __init__(self, users: dict[int, UserOut]) -> None:
        self.users = users

    async def get(self, user_id: int) -> UserOut | None:
        return self.users.get(user_id)


class DummyAuditLogService:
    async def log(self, **kwargs) -> None:
        return None


class DummyEventDispatcher:
    async def dispatch(self, events) -> None:
        return None


@dataclass(slots=True)
class DummyHardwareUseCases:
    calls: list[dict] = field(default_factory=list)

    async def add_files(self, *, hardware_id: int, files, audit):
        self.calls.append(
            {
                "hardware_id": hardware_id,
                "filenames": [file.filename for file in files],
                "actor_role": audit.user.role,
            }
        )
        return SimpleNamespace(
            files=[
                {
                    "id": 1,
                    "filename": "photo.png",
                    "file_type": "image/png",
                    "url": "/api/v1/hardware/files/1",
                }
            ],
            events=[],
        )


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_teacher_can_upload_hardware_files() -> None:
    teacher = make_user(user_id=7, role=UserRole.teacher)
    use_cases = DummyHardwareUseCases()

    app.dependency_overrides[get_user_service] = lambda: DummyUserService({7: teacher})
    app.dependency_overrides[get_audit_log_service] = lambda: DummyAuditLogService()
    app.dependency_overrides[get_inventory_hardware_use_cases] = lambda: use_cases
    app.dependency_overrides[get_inventory_event_dispatcher] = lambda: DummyEventDispatcher()

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(7))
            response = client.post(
                "/api/v1/hardware/42/files",
                headers={"Origin": "http://localhost:5173"},
                files=[("files", ("photo.png", b"image", "image/png"))],
            )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert use_cases.calls == [
            {
                "hardware_id": 42,
                "filenames": ["photo.png"],
                "actor_role": UserRole.teacher,
            }
        ]
    finally:
        clear_dependency_overrides()
