import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from modules.administration.models.audit_log import AuditLog
from modules.administration.repositories.audit_log import AuditLogRepository
from modules.administration.services.audit_log import AuditLogService
from modules.identity.public import UserSummary
from modules.identity.repositories.users import UserRepository


@pytest.fixture
def audit():
    repo = SimpleNamespace(add=AsyncMock(), list=AsyncMock())
    users = SimpleNamespace(get_summaries=AsyncMock(return_value={
        7: UserSummary(7, "teacher@example.ru", "Test", "User"),
    }))
    return AuditLogService(repo, users), repo, users


def entry(entry_id, user_id):
    return AuditLog(
        id=entry_id, user_id=user_id, created_at=datetime.now(UTC),
        action="hardware.update", entity_type="hardware", entity_id=10, payload={},
    )


def test_authors_are_loaded_once_and_deleted_users_remain_null(audit):
    service, repo, users = audit
    repo.list.return_value = ([entry(1, 7), entry(2, 7), entry(3, 8), entry(4, None)], 4)
    items, total = asyncio.run(service.list(limit=20, offset=0))
    users.get_summaries.assert_awaited_once_with({7, 8})
    repo.list.assert_awaited_once_with(limit=20, offset=0)
    assert total == 4
    assert items[0].user.email == "teacher@example.ru"
    assert items[0].user == items[1].user
    assert items[2].user is None and items[3].user is None
    assert set(items[0].user.model_dump()) == {"id", "email", "name", "surname"}


@pytest.mark.parametrize("anonymous", [False, True])
def test_empty_or_anonymous_page_does_not_load_users(audit, anonymous):
    service, repo, users = audit
    entries = [entry(1, None)] if anonymous else []
    repo.list.return_value = (entries, len(entries))
    asyncio.run(service.list())
    users.get_summaries.assert_not_awaited()


def test_log_masks_secrets_without_mutating_caller_payload(audit):
    service, repo, users = audit
    payload = {"nested": {"password": "private", "state": False}}
    result = asyncio.run(service.log(
        user_id=7, action="hardware.update", entity_type="hardware",
        payload=payload, ip="192.0.2.1", path="/api/hardware/10", method="PUT",
    ))
    saved = repo.add.call_args.args[0]
    assert saved.payload == {"nested": {"password": "***", "state": False}}
    assert payload["nested"]["password"] == "private"
    assert (saved.user_id, saved.ip, saved.method) == (7, "192.0.2.1", "PUT")
    assert result is None
    users.get_summaries.assert_not_awaited()


def test_write_failure_propagates_to_request_transaction(audit):
    service, repo, _ = audit
    repo.add.side_effect = RuntimeError("flush failed")
    with pytest.raises(RuntimeError, match="flush failed"):
        asyncio.run(service.log(user_id=7, action="update", entity_type="hardware"))


def test_repository_flushes_without_owning_transaction():
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock())
    record = entry(1, 7)
    assert asyncio.run(AuditLogRepository(db).add(record)) is record
    db.add.assert_called_once_with(record)
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


def test_identity_summary_query_selects_only_public_columns():
    row = SimpleNamespace(id=7, _mapping={
        "id": 7, "email": "teacher@example.ru", "name": "Test", "surname": "User",
    })
    db = SimpleNamespace(execute=AsyncMock(return_value=[row]))
    repo = UserRepository(db)
    assert asyncio.run(repo.get_summaries(set())) == {}
    db.execute.assert_not_awaited()
    summaries = asyncio.run(repo.get_summaries({7}))
    statement = db.execute.call_args.args[0]
    assert [column.name for column in statement.selected_columns] == ["id", "email", "name", "surname"]
    assert summaries == {7: UserSummary(**row._mapping)}


def test_audit_pagination_has_a_unique_tiebreaker():
    items = Mock()
    items.scalars.return_value.all.return_value = []
    count = Mock()
    count.scalar_one.return_value = 0
    db = SimpleNamespace(execute=AsyncMock(side_effect=[items, count]))
    assert asyncio.run(AuditLogRepository(db).list(limit=2, offset=4)) == ([], 0)
    sql = str(db.execute.call_args_list[0].args[0])
    assert "ORDER BY audit_logs.created_at DESC, audit_logs.id DESC" in sql
