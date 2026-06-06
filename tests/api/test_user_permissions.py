from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from dependencies.audit_actor import get_user_audit_actor
from dependencies.user import get_user_service
from main import app
from models.user import UserRole
from schemas.user import UserOut
from utils.tokens import issue_access_token


def make_user(
    *,
    user_id: int,
    role: UserRole,
    is_superuser: bool = False,
) -> UserOut:
    return UserOut(
        id=user_id,
        email=f"user{user_id}@example.com",
        name="Alex",
        surname="Ivanov",
        photo=None,
        role=role,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=is_superuser,
    )


class DummyUserService:
    def __init__(self, users: dict[int, UserOut]) -> None:
        self.users = users
        self.updated: list[tuple[int, dict]] = []

    async def get(self, user_id: int) -> UserOut | None:
        return self.users.get(user_id)

    async def get_all(self) -> list[UserOut]:
        return list(self.users.values())

    async def update(self, user_id: int, user_in):
        changes = user_in.model_dump(exclude_unset=True)
        self.updated.append((user_id, changes))

        user = self.users[user_id]
        updated = user.model_copy(update=changes)
        self.users[user_id] = updated
        return updated


@dataclass(slots=True)
class DummyUserAudit:
    user: UserOut
    meta: dict = field(
        default_factory=lambda: {
            "ip": "127.0.0.1",
            "user_agent": "pytest",
            "path": "/api/v1/users/1",
            "method": "PATCH",
        }
    )
    logs: list[dict] = field(default_factory=list)

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


def override_user_service(user_service: DummyUserService) -> None:
    app.dependency_overrides[get_user_service] = lambda: user_service


def override_update_dependencies(*, user_service: DummyUserService, audit: DummyUserAudit) -> None:
    override_user_service(user_service)
    app.dependency_overrides[get_user_audit_actor] = lambda: audit


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_users_me_requires_authentication() -> None:
    override_user_service(DummyUserService({}))

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    finally:
        clear_dependency_overrides()


def test_users_me_returns_authenticated_user() -> None:
    user = make_user(user_id=7, role=UserRole.teacher)
    override_user_service(DummyUserService({7: user}))

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(7))
            response = client.get("/api/v1/users/me")

        assert response.status_code == 200
        assert response.json()["id"] == 7
        assert response.json()["role"] == UserRole.teacher.value
    finally:
        clear_dependency_overrides()


def test_users_all_rejects_teacher_role() -> None:
    teacher = make_user(user_id=7, role=UserRole.teacher)
    override_user_service(DummyUserService({7: teacher}))

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(7))
            response = client.get("/api/v1/users/all")

        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    finally:
        clear_dependency_overrides()


def test_users_all_allows_admin_role() -> None:
    admin = make_user(user_id=1, role=UserRole.admin)
    teacher = make_user(user_id=7, role=UserRole.teacher)
    override_user_service(DummyUserService({1: admin, 7: teacher}))

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(1))
            response = client.get("/api/v1/users/all")

        assert response.status_code == 200
        assert {item["id"] for item in response.json()} == {1, 7}
    finally:
        clear_dependency_overrides()


def test_read_user_allows_self_but_rejects_other_for_teacher() -> None:
    teacher = make_user(user_id=7, role=UserRole.teacher)
    other = make_user(user_id=8, role=UserRole.teacher)
    override_user_service(DummyUserService({7: teacher, 8: other}))

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(7))

            self_response = client.get("/api/v1/users/7")
            other_response = client.get("/api/v1/users/8")

        assert self_response.status_code == 200
        assert self_response.json()["id"] == 7
        assert other_response.status_code == 403
        assert other_response.json()["detail"] == "Not enough permissions"
    finally:
        clear_dependency_overrides()


def test_read_user_allows_admin_to_access_other_user() -> None:
    admin = make_user(user_id=1, role=UserRole.admin)
    teacher = make_user(user_id=8, role=UserRole.teacher)
    override_user_service(DummyUserService({1: admin, 8: teacher}))

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(1))
            response = client.get("/api/v1/users/8")

        assert response.status_code == 200
        assert response.json()["id"] == 8
    finally:
        clear_dependency_overrides()


def test_update_user_rejects_non_admin_updating_other_user() -> None:
    current_user = make_user(user_id=7, role=UserRole.teacher)
    target_user = make_user(user_id=8, role=UserRole.teacher)
    service = DummyUserService({8: target_user})
    audit = DummyUserAudit(user=current_user)
    override_update_dependencies(user_service=service, audit=audit)

    try:
        with TestClient(app) as client:
            response = client.patch("/api/v1/users/8", json={"name": "Updated"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
        assert service.updated == []
        assert audit.logs == []
    finally:
        clear_dependency_overrides()


def test_update_user_rejects_admin_updating_another_superuser() -> None:
    admin = make_user(user_id=1, role=UserRole.admin, is_superuser=False)
    target_superuser = make_user(user_id=2, role=UserRole.admin, is_superuser=True)
    service = DummyUserService({2: target_superuser})
    audit = DummyUserAudit(user=admin)
    override_update_dependencies(user_service=service, audit=audit)

    try:
        with TestClient(app) as client:
            response = client.patch("/api/v1/users/2", json={"surname": "Updated"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Can't change another superuser"
        assert service.updated == []
        assert audit.logs == []
    finally:
        clear_dependency_overrides()


def test_update_user_strips_role_when_regular_user_updates_self() -> None:
    current_user = make_user(user_id=7, role=UserRole.teacher)
    service = DummyUserService({7: current_user})
    audit = DummyUserAudit(user=current_user)
    override_update_dependencies(user_service=service, audit=audit)

    try:
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/users/7",
                json={"name": "Updated", "role": UserRole.admin.value},
            )

        assert response.status_code == 200
        assert response.json()["id"] == 7
        assert response.json()["name"] == "Updated"
        assert response.json()["role"] == UserRole.teacher.value
        assert len(service.updated) == 1
        assert service.updated[0][0] == 7
        assert service.updated[0][1]["name"] == "Updated"
        assert "role" not in service.updated[0][1]
        assert audit.logs[0]["action"] == "user.update"
        assert "name" in audit.logs[0]["payload"]["changed_fields"]
        assert "role" not in audit.logs[0]["payload"]["changed_fields"]
    finally:
        clear_dependency_overrides()
