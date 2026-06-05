from dataclasses import dataclass
from collections.abc import Sequence

from loguru import logger

from core.exceptions import HardwareNotFoundError, HardwarePermissionDeniedError
from models import Hardware
from models.user import UserRole
from schemas.hardware import HardwareUpdate
from schemas.hardware_file import HardwareFileResponse
from modules.inventory.events import (
    AudienceUpdatedEvent,
    HardwareStateChangedEvent,
    InventoryEvent,
)
from modules.inventory.ports import (
    AuditLogger,
    HardwareFileServicePort,
    HardwareServicePort,
    InventoryActor,
    UploadedHardwareFile,
)
from utils.audit import clean_sensitive


@dataclass(slots=True, frozen=True)
class AddHardwareFilesResult:
    files: list[HardwareFileResponse]
    events: list[InventoryEvent]


@dataclass(slots=True, frozen=True)
class UpdateHardwareResult:
    hardware: Hardware
    events: list[InventoryEvent]


@dataclass(slots=True, frozen=True)
class DeleteHardwareFileResult:
    audience_id: int
    events: list[InventoryEvent]


class InventoryHardwareUseCases:
    def __init__(
        self,
        hardware_service: HardwareServicePort,
        hardware_file_service: HardwareFileServicePort | None = None,
    ) -> None:
        self.hardware_service = hardware_service
        self.hardware_file_service = hardware_file_service

    async def add_files(
        self,
        *,
        hardware_id: int,
        files: Sequence[UploadedHardwareFile],
        audit: AuditLogger,
    ) -> AddHardwareFilesResult:
        result = await self._hardware_file_service().update_files(hardware_id, files)
        logger.info(
            "Hardware files processed: hardware_id={} audience_id={} requested={} saved={}",
            hardware_id,
            result.audience_id,
            len(files),
            len(result.files),
        )

        await audit.log(
            action="hardware.file_add",
            entity_type="hardware",
            entity_id=hardware_id,
            payload={
                "audience_id": result.audience_id,
                "files_count": len(files),
                "filenames": [file.filename for file in files][:10],
            },
        )

        return AddHardwareFilesResult(
            files=result.files,
            events=[AudienceUpdatedEvent(result.audience_id)],
        )

    async def update_hardware(
        self,
        *,
        hardware_id: int,
        data: HardwareUpdate,
        actor: InventoryActor,
        audit: AuditLogger,
    ) -> UpdateHardwareResult:
        current_hw = await self.hardware_service.get(hardware_id)
        if not current_hw:
            raise HardwareNotFoundError()

        if data.state is True and actor.role == UserRole.teacher:
            logger.warning(
                "Hardware update rejected: teacher tried to mark good state user_id={} hardware_id={}",
                actor.id,
                hardware_id,
            )
            raise HardwarePermissionDeniedError("Teacher can't mark hardware as good state")

        if actor.role == UserRole.teacher:
            data = HardwareUpdate(**data.model_dump(include={"state"}, exclude_unset=True))
        data = self._normalize_update(data)

        previous_state = current_hw.state
        updated_hw = await self.hardware_service.update(hardware_id, data)
        state_changed = previous_state != updated_hw.state

        await audit.log(
            action="hardware.update",
            entity_type="hardware",
            entity_id=hardware_id,
            payload={
                "audience_id": updated_hw.audience_id,
                **(clean_sensitive(data) or {}),
            },
        )

        events: list[InventoryEvent] = [
            AudienceUpdatedEvent(
                updated_hw.audience_id,
                notify_subscribers=not state_changed,
            )
        ]
        if state_changed:
            events.append(
                HardwareStateChangedEvent(
                    previous_state=previous_state,
                    hardware=updated_hw,
                    actor_user_id=actor.id,
                )
            )

        return UpdateHardwareResult(
            hardware=updated_hw,
            events=events,
        )

    async def delete_file(
        self,
        *,
        file_id: int,
        audit: AuditLogger,
    ) -> DeleteHardwareFileResult:
        result = await self._hardware_file_service().delete_file(file_id)
        logger.info("Hardware file deleted: file_id={} audience_id={}", file_id, result.audience_id)

        await audit.log(
            action="hardware.file_delete",
            entity_type="hardware_file",
            entity_id=file_id,
            payload={"audience_id": result.audience_id},
        )

        return DeleteHardwareFileResult(
            audience_id=result.audience_id,
            events=[AudienceUpdatedEvent(result.audience_id)],
        )

    def _hardware_file_service(self) -> HardwareFileServicePort:
        if self.hardware_file_service is None:
            raise RuntimeError("Hardware file service is not configured")
        return self.hardware_file_service

    @staticmethod
    def _normalize_update(data: HardwareUpdate) -> HardwareUpdate:
        if data.state is not True:
            return data

        update_data = data.model_dump(exclude_unset=True)
        update_data["description"] = None
        return HardwareUpdate(**update_data)
