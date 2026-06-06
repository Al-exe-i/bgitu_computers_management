from datetime import datetime, timezone

from fastapi.testclient import TestClient

from dependencies.invite import get_invite_service
from dependencies.user import get_user_service
from main import app
from models.user import UserRole
from schemas.invite import InviteListItem
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

    async def get(self, user_id: int) -> UserOut | None:
        return self.users.get(user_id)


class DummyInviteService:
    def __init__(self, invites: list[InviteListItem]) -> None:
        self.invites = invites

    async def list_all(self) -> list[InviteListItem]:
        return self.invites


def override_dependencies(*, user_service: DummyUserService, invite_service: DummyInviteService) -> None:
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_invite_service] = lambda: invite_service


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_admin_invites_requires_authentication() -> None:
    override_dependencies(
        user_service=DummyUserService({}),
        invite_service=DummyInviteService([]),
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/admin/invites")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    finally:
        clear_dependency_overrides()


def test_admin_invites_rejects_teacher_role() -> None:
    teacher = make_user(user_id=7, role=UserRole.teacher)
    override_dependencies(
        user_service=DummyUserService({7: teacher}),
        invite_service=DummyInviteService([]),
    )

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(7))
            response = client.get("/api/v1/admin/invites")

        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    finally:
        clear_dependency_overrides()


def test_admin_invites_allows_admin_role() -> None:
    admin = make_user(user_id=1, role=UserRole.admin)
    invites = [
        InviteListItem(
            id=5,
            target_email="invite@example.com",
            target_role=UserRole.teacher,
            note="test",
            created_by_user_id=1,
            created_at=datetime(2026, 4, 21, tzinfo=timezone.utc),
            expires_at=datetime(2026, 4, 28, tzinfo=timezone.utc),
            used_at=None,
            revoked_at=None,
            used_by_user_id=None,
        )
    ]
    override_dependencies(
        user_service=DummyUserService({1: admin}),
        invite_service=DummyInviteService(invites),
    )

    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", issue_access_token(1))
            response = client.get("/api/v1/admin/invites")

        assert response.status_code == 200
        assert response.json() == [
            {
                "id": 5,
                "target_email": "invite@example.com",
                "target_role": UserRole.teacher.value,
                "note": "test",
                "created_by_user_id": 1,
                "created_at": "2026-04-21T00:00:00Z",
                "expires_at": "2026-04-28T00:00:00Z",
                "used_at": None,
                "revoked_at": None,
                "used_by_user_id": None,
            }
        ]
    finally:
        clear_dependency_overrides()
