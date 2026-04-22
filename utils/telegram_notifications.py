from typing import Protocol

from fastapi import BackgroundTasks

from core.config import settings
from schemas.telegram import TelegramEventType
from tasks.notifications import send_hardware_state_notification


class HardwareStatePayload(Protocol):
    id: int
    audience_id: int
    state: bool
    title: str | None
    inv_number: str | None


def enqueue_hardware_state_notification(
    background_tasks: BackgroundTasks,
    *,
    previous_state: bool,
    hardware: HardwareStatePayload,
) -> None:
    if not settings.telegram.enabled:
        return

    if previous_state == hardware.state:
        return

    event_type = (
        TelegramEventType.hardware_fault
        if previous_state and not hardware.state
        else TelegramEventType.hardware_recovered
    )

    background_tasks.add_task(
        send_hardware_state_notification.delay,
        hardware_id=hardware.id,
        audience_id=hardware.audience_id,
        event_type=event_type.value,
        title=hardware.title,
        inv_number=hardware.inv_number,
    )
