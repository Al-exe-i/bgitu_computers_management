from types import SimpleNamespace

from fastapi import BackgroundTasks

from core.config import settings
from tasks.notifications import send_hardware_state_notification
from utils.telegram_notifications import enqueue_hardware_state_notification


def test_enqueue_hardware_state_notification_adds_fault_task(monkeypatch) -> None:
    monkeypatch.setattr(settings.telegram, "enabled", True)
    background_tasks = BackgroundTasks()
    hardware = SimpleNamespace(
        id=9,
        audience_id=12,
        state=False,
        type=SimpleNamespace(value="computer"),
        title="Монитор",
        description="Полосы на экране",
        inv_number="MON-1",
        x=4,
        y=2,
    )

    enqueue_hardware_state_notification(
        background_tasks,
        previous_state=True,
        hardware=hardware,
    )

    assert len(background_tasks.tasks) == 1
    task = background_tasks.tasks[0]
    assert task.func == send_hardware_state_notification.delay
    assert task.kwargs == {
        "hardware_id": 9,
        "audience_id": 12,
        "event_type": "hardware_fault",
        "hardware_type": "computer",
        "title": "Монитор",
        "description": "Полосы на экране",
        "inv_number": "MON-1",
        "x": 4,
        "y": 2,
    }


def test_enqueue_hardware_state_notification_skips_when_state_is_unchanged(monkeypatch) -> None:
    monkeypatch.setattr(settings.telegram, "enabled", True)
    background_tasks = BackgroundTasks()
    hardware = SimpleNamespace(
        id=9,
        audience_id=12,
        state=True,
        type=SimpleNamespace(value="computer"),
        title="Монитор",
        description="Полосы на экране",
        inv_number="MON-1",
        x=4,
        y=2,
    )

    enqueue_hardware_state_notification(
        background_tasks,
        previous_state=True,
        hardware=hardware,
    )

    assert background_tasks.tasks == []
