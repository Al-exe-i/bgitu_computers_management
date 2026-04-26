from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from core.exceptions import TelegramAccountNotLinkedError, TelegramSubscriptionAlreadyExistsError
from dependencies.audit_actor import get_user_audit_actor
from dependencies.telegram import get_telegram_integration_use_cases
from main import app
from models.user import UserRole
from schemas.user import UserOut


def make_user() -> UserOut:
    return UserOut(
        id=7,
        email="user7@example.com",
        name="Alex",
        surname="Ivanov",
        telegram_id=None,
        telegram_id_confirmed=False,
        photo=None,
        role=UserRole.teacher,
        reg_date=datetime(2026, 4, 21, tzinfo=timezone.utc),
        is_superuser=False,
    )


@dataclass(slots=True)
class DummyAudit:
    user: UserOut
    meta: dict = field(default_factory=dict)
    logs: list[dict] = field(default_factory=list)

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


class DummyTelegramUseCases:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    async def create_subscription(self, **_kwargs):
        raise self.exc


def override_dependencies(exc: Exception) -> None:
    app.dependency_overrides[get_user_audit_actor] = lambda: DummyAudit(user=make_user())
    app.dependency_overrides[get_telegram_integration_use_cases] = lambda: DummyTelegramUseCases(exc)


def clear_dependency_overrides() -> None:
    app.dependency_overrides.clear()


def test_create_telegram_subscription_maps_not_linked_to_400() -> None:
    override_dependencies(TelegramAccountNotLinkedError())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/telegram/subscriptions",
                json={
                    "scope_type": "audience",
                    "scope_id": 12,
                    "event_type": "hardware_fault",
                    "delivery_mode": "immediate",
                },
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Telegram account is not linked"
    finally:
        clear_dependency_overrides()


def test_create_telegram_subscription_maps_duplicate_to_409() -> None:
    override_dependencies(TelegramSubscriptionAlreadyExistsError())

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/telegram/subscriptions",
                json={
                    "scope_type": "audience",
                    "scope_id": 12,
                    "event_type": "hardware_fault",
                    "delivery_mode": "immediate",
                },
            )

        assert response.status_code == 409
        assert response.json()["detail"] == "Telegram subscription already exists"
    finally:
        clear_dependency_overrides()
