import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("first_import", [
    "modules.identity.models.invite_link", "modules.identity.models.user",
    "modules.identity.public", "modules.inventory.models.hardware", "db.session",
    "modules.inventory.models.audience", "modules.inventory.public",
    "modules.notifications.models.subscription", "modules.notifications.public",
    "modules.administration.models.audit_log", "modules.administration.public",
])
def test_registry_is_complete_regardless_of_import_order(first_import):
    # A fresh interpreter exposes circular imports hidden by pytest's module cache.
    result = subprocess.run(
        [sys.executable, "-c", f"""
import {first_import}
from db.base import Base
from sqlalchemy.orm import configure_mappers
configure_mappers()
from modules.administration.models.audit_log import AuditLog
assert not AuditLog.__mapper__.relationships
assert set(Base.metadata.tables) == {{
    'audiences', 'audit_logs', 'hardware_files', 'hardwares', 'invite_links',
    'notification_subscriptions', 'offices', 'spec_templates', 'used_refresh_tokens',
    'user_sessions', 'users', 'floor_plans',
}}
for table in Base.metadata.tables.values():
    for foreign_key in table.foreign_keys:
        assert foreign_key.column is not None
assert Base.metadata.tables['users'].c.role.type.enums == ['admin', 'teacher']
assert Base.metadata.tables['hardwares'].c.type.type.enums == [
    'computer', 'tv', 'projector', 'printer', 'switch', 'router', 'server', 'other',
]
"""],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
