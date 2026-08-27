import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from core.exceptions import SpecTemplateNotFoundError
from models.hardware import HardwareType
from modules.inventory.application import InventorySpecTemplateUseCases
from schemas.spec_template import SpecTemplateCreate, SpecTemplateUpdate


class FakeSpecTemplateService:
    def __init__(self) -> None:
        self.template = SimpleNamespace(
            id=3,
            name="Рабочая станция",
            hardware_type="computer",
            specs={"cpu_cores": 8},
            created_at=datetime(2026, 8, 27, tzinfo=UTC),
        )

    async def list(self, hardware_type=None):
        return [self.template]

    async def get(self, template_id: int):
        return self.template if template_id == self.template.id else None

    async def create(self, data):
        return self.template

    async def update(self, template_id: int, data):
        if template_id != self.template.id:
            return None
        if data.name is not None:
            self.template.name = data.name
        return self.template

    async def delete(self, template_id: int):
        return template_id == self.template.id


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs):
        self.logs.append(kwargs)


def test_create_template_returns_dto_and_writes_audit() -> None:
    async def scenario() -> None:
        audit = FakeAudit()
        use_cases = InventorySpecTemplateUseCases(FakeSpecTemplateService())

        result = await use_cases.create_template(
            data=SpecTemplateCreate(
                name="Рабочая станция",
                hardware_type=HardwareType.computer,
                specs={"cpu_cores": 8},
            ),
            audit=audit,
        )

        assert result.id == 3
        assert audit.logs[0]["action"] == "spec_template.create"

    asyncio.run(scenario())


def test_update_missing_template_raises_domain_error() -> None:
    async def scenario() -> None:
        use_cases = InventorySpecTemplateUseCases(FakeSpecTemplateService())

        with pytest.raises(SpecTemplateNotFoundError):
            await use_cases.update_template(
                template_id=99,
                data=SpecTemplateUpdate(name="Нет"),
                audit=FakeAudit(),
            )

    asyncio.run(scenario())
