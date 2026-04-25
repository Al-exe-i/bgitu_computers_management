from typing import Protocol

from fastapi import BackgroundTasks

from core.config import settings
from schemas.telegram import TelegramEventType
from tasks.notifications import (
    send_auth_security_notification,
    send_hardware_state_notification,
)


class HardwareStatePayload(Protocol):
    id: int
    audience_id: int
    state: bool
    type: object
    title: str | None
    description: str | None
    inv_number: str | None
    x: int
    y: int


def enqueue_hardware_state_notification(
    background_tasks: BackgroundTasks,
    *,
    previous_state: bool,
    hardware: HardwareStatePayload,
    actor_user_id: int | None = None,
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
        hardware_type=getattr(hardware.type, "value", hardware.type),
        title=hardware.title,
        description=hardware.description,
        inv_number=hardware.inv_number,
        x=hardware.x,
        y=hardware.y,
        actor_user_id=actor_user_id,
    )


def enqueue_auth_security_notification(
    background_tasks: BackgroundTasks,
    *,
    user_id: int,
    event_name: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    if not settings.telegram.enabled:
        return

    background_tasks.add_task(
        send_auth_security_notification.delay,
        user_id=user_id,
        event_name=event_name,
        ip=ip,
        user_agent=user_agent,
    )
