import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from core.exceptions.management import ManagementUserError
from db.bootstrap_lock import PostgresBootstrapLock
from modules.identity.models.user import User
from modules.identity.repositories.users import UserRepository
from modules.inventory.repositories.bootstrap import OfficeBootstrapRepository


def test_password_reset_increments_version_in_sql_and_returns_updated_user():
    result = MagicMock()
    result.scalar_one_or_none.return_value = object()
    db = MagicMock(execute=AsyncMock(return_value=result))
    user = asyncio.run(
        UserRepository(db).reset_managed_password("admin@example.ru", "hash")
    )
    statement = db.execute.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "access_token_version=(users.access_token_version +" in sql
    assert "lower(users.email)" in sql and "users.id" in sql.split("RETURNING", 1)[1]
    assert statement.get_execution_options()["populate_existing"] is True
    assert user is result.scalar_one_or_none.return_value


@pytest.mark.parametrize("constraint", ["uq_users_email_ci", "other_constraint"])
def test_only_email_unique_violation_is_translated(constraint):
    original = Exception("database failure")
    original.constraint_name = constraint
    adapted = Exception("driver wrapper")
    adapted.__cause__ = original
    error = IntegrityError("INSERT", {}, adapted)
    db = MagicMock(flush=AsyncMock(side_effect=error))
    expected = (
        ManagementUserError if constraint == "uq_users_email_ci" else IntegrityError
    )
    with pytest.raises(expected):
        asyncio.run(UserRepository(db).create_managed(User(email="admin@example.ru")))
    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_seed_uses_transaction_scoped_lock():
    db = MagicMock(execute=AsyncMock())
    asyncio.run(PostgresBootstrapLock(db).acquire())
    statement, parameters = db.execute.call_args.args
    assert "pg_advisory_xact_lock" in str(statement)
    assert parameters == {"lock_id": 4_244_748_214_403_238_731}


def test_office_seed_sequence_never_moves_backwards():
    db = MagicMock(execute=AsyncMock())
    repo = OfficeBootstrapRepository(db)
    asyncio.run(repo.lock())
    asyncio.run(repo.synchronize_sequence())
    statements = [str(call.args[0]) for call in db.execute.call_args_list]
    assert "LOCK TABLE offices IN SHARE ROW EXCLUSIVE MODE" in statements[0]
    assert all(
        part in statements[1]
        for part in ["setval", "GREATEST", "MAX(id)", "pg_sequence_last_value"]
    )
