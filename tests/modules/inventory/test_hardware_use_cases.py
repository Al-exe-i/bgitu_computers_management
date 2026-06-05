import asyncio
from types import SimpleNamespace

import pytest

from core.exceptions import HardwarePermissionDeniedError
from models.user import UserRole
from modules.inventory.application import InventoryHardwareUseCases
from modules.inventory.events import AudienceUpdatedEvent, HardwareStateChangedEvent
from schemas.hardware import HardwareUpdate


class FakeHardwareService:
    def __init__(self, hardware):
        self.hardware = hardware
        self.update_calls: list[dict] = []

    async def get(self, hardware_id: int):
        if self.hardware and self.hardware.id == hardware_id:
            return self.hardware
        return None

    async def update(self, hardware_id: int, schema: HardwareUpdate):
        self.update_calls.append(
            {
                "hardware_id": hardware_id,
                "data": schema.model_dump(exclude_unset=True),
            }
        )
        changes = schema.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(self.hardware, key, value)
        return self.hardware


class FakeHardwareFileService:
    def __init__(self) -> None:
        self.update_calls: list[dict] = []
        self.delete_calls: list[int] = []
        self.files = [
            SimpleNamespace(
                id=3,
                hardware_id=9,
                file_path="uploads/photo.png",
                file_type="image/png",
            )
        ]
        self.audience_id = 12

    async def update_files(self, hardware_id: int, files):
        self.update_calls.append(
            {
                "hardware_id": hardware_id,
                "filenames": [file.filename for file in files],
            }
        )
        return SimpleNamespace(files=self.files, audience_id=self.audience_id)

    async def delete_file(self, file_id: int):
        self.delete_calls.append(file_id)
        return SimpleNamespace(audience_id=self.audience_id)


class FakeAudit:
    def __init__(self) -> None:
        self.logs: list[dict] = []

    async def log(self, **kwargs):
        self.logs.append(kwargs)


def make_hardware(**overrides):
    data = {
        "id": 9,
        "audience_id": 12,
        "state": True,
        "type": "computer",
        "title": "PC-1",
        "description": None,
        "inv_number": "INV-1",
        "x": 0,
        "y": 1,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_actor(*, role: UserRole):
    return SimpleNamespace(id=7, role=role, is_superuser=False)


def test_update_hardware_logs_audit_and_returns_inventory_events() -> None:
    async def scenario() -> None:
        hardware = make_hardware(state=True)
        service = FakeHardwareService(hardware)
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(service)

        result = await use_cases.update_hardware(
            hardware_id=9,
            data=HardwareUpdate(state=False, description="broken"),
            actor=make_actor(role=UserRole.admin),
            audit=audit,
        )

        assert result.hardware.state is False
        assert service.update_calls == [
            {
                "hardware_id": 9,
                "data": {"state": False, "description": "broken"},
            }
        ]
        assert audit.logs[0]["action"] == "hardware.update"
        assert audit.logs[0]["payload"]["audience_id"] == 12
        assert result.events[0] == AudienceUpdatedEvent(audience_id=12, notify_subscribers=False)
        assert isinstance(result.events[1], HardwareStateChangedEvent)
        assert result.events[1].previous_state is True
        assert result.events[1].actor_user_id == 7

    asyncio.run(scenario())


def test_update_hardware_without_state_change_returns_only_audience_event() -> None:
    async def scenario() -> None:
        hardware = make_hardware(state=True, description="old")
        service = FakeHardwareService(hardware)
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(service)

        result = await use_cases.update_hardware(
            hardware_id=9,
            data=HardwareUpdate(description="new"),
            actor=make_actor(role=UserRole.admin),
            audit=audit,
        )

        assert result.hardware.description == "new"
        assert result.events == [AudienceUpdatedEvent(audience_id=12, notify_subscribers=True)]

    asyncio.run(scenario())


def test_add_hardware_files_uses_file_service_and_logs_audit() -> None:
    async def scenario() -> None:
        file_service = FakeHardwareFileService()
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(
            FakeHardwareService(make_hardware()),
            file_service,
        )
        files = [SimpleNamespace(filename="photo.png")]

        result = await use_cases.add_files(
            hardware_id=9,
            files=files,
            audit=audit,
        )

        assert result.files == file_service.files
        assert file_service.update_calls == [
            {"hardware_id": 9, "filenames": ["photo.png"]}
        ]
        assert audit.logs[0]["action"] == "hardware.file_add"
        assert audit.logs[0]["payload"] == {
            "audience_id": 12,
            "files_count": 1,
            "filenames": ["photo.png"],
        }
        assert result.events == [AudienceUpdatedEvent(audience_id=12)]

    asyncio.run(scenario())


def test_update_hardware_rejects_teacher_marking_good_state() -> None:
    async def scenario() -> None:
        service = FakeHardwareService(make_hardware(state=False))
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(service)

        with pytest.raises(HardwarePermissionDeniedError):
            await use_cases.update_hardware(
                hardware_id=9,
                data=HardwareUpdate(state=True),
                actor=make_actor(role=UserRole.teacher),
                audit=audit,
            )

        assert service.update_calls == []
        assert audit.logs == []

    asyncio.run(scenario())


def test_update_hardware_marking_good_clears_description_in_use_case() -> None:
    async def scenario() -> None:
        hardware = make_hardware(state=False, description="broken")
        service = FakeHardwareService(hardware)
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(service)

        result = await use_cases.update_hardware(
            hardware_id=9,
            data=HardwareUpdate(state=True),
            actor=make_actor(role=UserRole.admin),
            audit=audit,
        )

        assert result.hardware.description is None
        assert service.update_calls == [
            {
                "hardware_id": 9,
                "data": {"state": True, "description": None},
            }
        ]

    asyncio.run(scenario())


def test_delete_hardware_file_uses_file_service_and_logs_audit() -> None:
    async def scenario() -> None:
        file_service = FakeHardwareFileService()
        audit = FakeAudit()
        use_cases = InventoryHardwareUseCases(
            FakeHardwareService(make_hardware()),
            file_service,
        )

        result = await use_cases.delete_file(
            file_id=3,
            audit=audit,
        )

        assert result.audience_id == 12
        assert file_service.delete_calls == [3]
        assert audit.logs[0] == {
            "action": "hardware.file_delete",
            "entity_type": "hardware_file",
            "entity_id": 3,
            "payload": {"audience_id": 12},
        }
        assert result.events == [AudienceUpdatedEvent(audience_id=12)]

    asyncio.run(scenario())
