import asyncio
from datetime import datetime, timezone

import pytest

from models.user import UserRole
from modules.identity.application import IdentityInviteUseCases
from schemas.invite import (
    InviteCreateBatch,
    InviteCreateOne,
    InviteCreateResult,
    InviteListItem,
)


EXPIRES_AT = datetime(2026, 4, 28, tzinfo=timezone.utc)


class FakeInviteService:
    def __init__(self) -> None:
        self.create_one_calls: list[dict] = []
        self.create_batch_calls: list[dict] = []
        self.deleted_ids: list[int] = []

    async def create_one(self, *, created_by_user_id: int, schema: InviteCreateOne) -> InviteCreateResult:
        self.create_one_calls.append(
            {
                "created_by_user_id": created_by_user_id,
                "schema": schema,
            }
        )
        return InviteCreateResult(
            id=5,
            invite_url="https://frontend/register?invite=token",
            target_email=schema.target_email,
            target_role=schema.target_role,
            expires_at=schema.expires_at,
            note=schema.note,
        )

    async def create_batch(self, *, created_by_user_id: int, schema: InviteCreateBatch) -> list[InviteCreateResult]:
        self.create_batch_calls.append(
            {
                "created_by_user_id": created_by_user_id,
                "schema": schema,
            }
        )
        return [
            InviteCreateResult(
                id=5,
                invite_url="https://frontend/register?invite=token",
                target_email=email,
                target_role=schema.target_role,
                expires_at=schema.expires_at,
                note=schema.note,
            )
            for email in (schema.emails or ["first@example.com", "second@example.com"])
        ]

    async def list_all(self) -> list[InviteListItem]:
        return [self._list_item(invite_id=5)]

    async def revoke(self, invite_id: int) -> InviteListItem:
        return self._list_item(invite_id=invite_id)

    async def delete(self, invite_id: int) -> None:
        self.deleted_ids.append(invite_id)

    @staticmethod
    def _list_item(invite_id: int) -> InviteListItem:
        return InviteListItem(
            id=invite_id,
            target_email="invite@example.com",
            target_role=UserRole.teacher,
            note="note",
            created_by_user_id=1,
            created_at=datetime(2026, 4, 21, tzinfo=timezone.utc),
            expires_at=EXPIRES_AT,
            used_at=None,
            revoked_at=None,
            used_by_user_id=None,
        )


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs) -> None:
        self.logs.append(kwargs)


@pytest.fixture
def audit() -> FakeAudit:
    return FakeAudit()


def test_create_one_invite_writes_audit_payload(audit: FakeAudit) -> None:
    async def scenario() -> None:
        service = FakeInviteService()
        use_cases = IdentityInviteUseCases(service)
        data = InviteCreateOne(
            target_email="invite@example.com",
            target_role=UserRole.teacher,
            expires_at=EXPIRES_AT,
            note="note",
        )

        result = await use_cases.create_one(
            data=data,
            created_by_user_id=1,
            audit=audit,
        )

        assert result.invite.id == 5
        assert service.create_one_calls[0]["created_by_user_id"] == 1
        assert audit.logs == [
            {
                "action": "invite.create",
                "entity_type": "invite",
                "entity_id": 5,
                "payload": {
                    "target_email": "invite@example.com",
                    "target_role": "teacher",
                    "expires_at": EXPIRES_AT.isoformat(),
                },
            }
        ]

    asyncio.run(scenario())


def test_create_batch_invite_writes_compact_audit_payload(audit: FakeAudit) -> None:
    async def scenario() -> None:
        service = FakeInviteService()
        use_cases = IdentityInviteUseCases(service)
        data = InviteCreateBatch(
            emails=["first@example.com", "second@example.com"],
            target_role=UserRole.teacher,
            expires_at=EXPIRES_AT,
        )

        result = await use_cases.create_batch(
            data=data,
            created_by_user_id=1,
            audit=audit,
        )

        assert len(result.invites) == 2
        assert service.create_batch_calls[0]["created_by_user_id"] == 1
        assert audit.logs == [
            {
                "action": "invite.create_batch",
                "entity_type": "invite",
                "payload": {
                    "created_count": 2,
                    "target_role": "teacher",
                    "targeted": True,
                    "targeted_emails_count": 2,
                    "expires_at": EXPIRES_AT.isoformat(),
                },
            }
        ]

    asyncio.run(scenario())


def test_revoke_and_delete_invite_write_audit(audit: FakeAudit) -> None:
    async def scenario() -> None:
        service = FakeInviteService()
        use_cases = IdentityInviteUseCases(service)

        revoked = await use_cases.revoke(invite_id=5, audit=audit)
        deleted = await use_cases.delete(invite_id=5, audit=audit)

        assert revoked.invite.id == 5
        assert deleted is not None
        assert service.deleted_ids == [5]
        assert audit.logs == [
            {
                "action": "invite.revoke",
                "entity_type": "invite",
                "entity_id": 5,
                "payload": {
                    "target_email": "invite@example.com",
                    "target_role": "teacher",
                },
            },
            {
                "action": "invite.delete",
                "entity_type": "invite",
                "entity_id": 5,
                "payload": {"invite_id": 5},
            },
        ]

    asyncio.run(scenario())
