import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from core.exceptions import InvalidUserPhotoError, UserPermissionDeniedError
from core.security import get_password_hash
from models.user import UserRole
from modules.identity.application.users import IdentityUserUseCases, PASSWORD_CHANGED_EVENT_NAME
from modules.identity.events import AuthSecurityNotificationEvent
from schemas.user import ChangePasswordSchema, UserOut, UserUpdate
from services.user_service import UserPhotoUpdateResult


def make_user(
    *,
    user_id: int,
    role: UserRole = UserRole.teacher,
    is_superuser: bool = False,
    photo: str | None = None,
) -> UserOut:
    return UserOut(
        id=user_id,
        email=f"user{user_id}@example.com",
        name="Alex",
        surname="Ivanov",
        photo=photo,
        role=role,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=is_superuser,
    )


@dataclass(slots=True)
class Actor:
    id: int
    role: UserRole
    is_superuser: bool = False
    password: str = field(default_factory=lambda: get_password_hash("oldpass"))


class FakeUserService:
    def __init__(self, users: dict[int, UserOut]) -> None:
        self.users = users
        self.updated: list[tuple[int, dict]] = []
        self.uploaded: list[int] = []

    async def get(self, user_id: int) -> UserOut | None:
        return self.users.get(user_id)

    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None:
        changes = data.model_dump(exclude_unset=True)
        self.updated.append((user_id, changes))

        user = self.users.get(user_id)
        if user is None:
            return None

        updated = user.model_copy(update=changes)
        self.users[user_id] = updated
        return updated

    async def verify_password(self, user_id: int, password: str) -> bool:
        return user_id in self.users and password == "oldpass"

    async def update_password(self, user_id: int, password: str) -> UserOut | None:
        self.updated.append((user_id, {"password": password}))
        return self.users.get(user_id)

    async def upload_photo(self, user_id: int, file) -> UserPhotoUpdateResult | None:
        self.uploaded.append(user_id)
        user = self.users.get(user_id)
        if user is None:
            return None

        updated = user.model_copy(update={"photo": "avatar.jpg"})
        self.users[user_id] = updated
        return UserPhotoUpdateResult(user=updated, had_photo=bool(user.photo))


class FakeAuthService:
    def __init__(self) -> None:
        self.logged_out_user_ids: list[int] = []

    async def logout_all(self, *, user_id: int) -> None:
        self.logged_out_user_ids.append(user_id)


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


@dataclass(slots=True)
class FakeUploadFile:
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes:
        return b"content"

    async def close(self) -> None:
        return None


@pytest.fixture
def audit() -> FakeAudit:
    return FakeAudit()


def test_regular_user_update_self_strips_role_and_logs_changed_fields(audit: FakeAudit) -> None:
    async def scenario() -> None:
        actor = Actor(id=7, role=UserRole.teacher)
        service = FakeUserService({7: make_user(user_id=7)})
        use_cases = IdentityUserUseCases(service, FakeAuthService())

        result = await use_cases.update_user(
            user_id=7,
            data=UserUpdate(name="Updated", role=UserRole.admin),
            actor=actor,
            audit=audit,
        )

        assert result.user.name == "Updated"
        assert result.user.role == UserRole.teacher
        assert service.updated == [(7, {"name": "Updated"})]
        assert audit.logs == [
            {
                "action": "user.update",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {
                    "target_user_id": 7,
                    "changed_fields": ["name"],
                },
            }
        ]

    asyncio.run(scenario())


def test_admin_cannot_update_another_superuser(audit: FakeAudit) -> None:
    async def scenario() -> None:
        actor = Actor(id=1, role=UserRole.admin)
        service = FakeUserService(
            {
                2: make_user(
                    user_id=2,
                    role=UserRole.admin,
                    is_superuser=True,
                )
            }
        )
        use_cases = IdentityUserUseCases(service, FakeAuthService())

        with pytest.raises(UserPermissionDeniedError) as exc:
            await use_cases.update_user(
                user_id=2,
                data=UserUpdate(surname="Updated"),
                actor=actor,
                audit=audit,
            )

        assert exc.value.detail == "Can't change another superuser"
        assert service.updated == []
        assert audit.logs == []

    asyncio.run(scenario())


def test_change_password_writes_audit_and_returns_security_event(audit: FakeAudit) -> None:
    async def scenario() -> None:
        actor = Actor(id=7, role=UserRole.teacher)
        service = FakeUserService({7: make_user(user_id=7)})
        auth_service = FakeAuthService()
        use_cases = IdentityUserUseCases(service, auth_service)

        result = await use_cases.change_password(
            data=ChangePasswordSchema(current_password="oldpass", new_password="newpass"),
            actor=actor,
            audit=audit,
            ip="127.0.0.1",
            user_agent="pytest",
        )

        assert service.updated == [(7, {"password": "newpass"})]
        assert auth_service.logged_out_user_ids == [7]
        assert audit.logs == [
            {
                "action": "user.password_change",
                "entity_type": "user",
                "entity_id": 7,
                "payload": {"target_user_id": 7},
            }
        ]
        assert result.events == [
            AuthSecurityNotificationEvent(
                user_id=7,
                event_name=PASSWORD_CHANGED_EVENT_NAME,
                ip="127.0.0.1",
                user_agent="pytest",
            )
        ]

    asyncio.run(scenario())


def test_invalid_photo_content_type_rejected_before_upload(audit: FakeAudit) -> None:
    async def scenario() -> None:
        actor = Actor(id=7, role=UserRole.teacher)
        service = FakeUserService({7: make_user(user_id=7)})
        use_cases = IdentityUserUseCases(service, FakeAuthService())

        with pytest.raises(InvalidUserPhotoError):
            await use_cases.upload_user_photo(
                user_id=7,
                file=FakeUploadFile(filename="notes.txt", content_type="text/plain"),
                actor=actor,
                audit=audit,
            )

        assert service.uploaded == []
        assert audit.logs == []

    asyncio.run(scenario())


def test_svg_photo_is_rejected_before_upload(audit: FakeAudit) -> None:
    async def scenario() -> None:
        actor = Actor(id=7, role=UserRole.teacher)
        service = FakeUserService({7: make_user(user_id=7)})
        use_cases = IdentityUserUseCases(service, FakeAuthService())

        with pytest.raises(InvalidUserPhotoError):
            await use_cases.upload_user_photo(
                user_id=7,
                file=FakeUploadFile(
                    filename="avatar.svg",
                    content_type="image/svg+xml",
                ),
                actor=actor,
                audit=audit,
            )

        assert service.uploaded == []

    asyncio.run(scenario())
