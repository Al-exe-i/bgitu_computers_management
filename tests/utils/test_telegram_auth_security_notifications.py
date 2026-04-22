from fastapi import BackgroundTasks

from core.config import settings
from tasks.notifications import send_auth_security_notification
from utils.telegram_notifications import enqueue_auth_security_notification


def test_enqueue_auth_security_notification_adds_task(monkeypatch) -> None:
    monkeypatch.setattr(settings.telegram, "enabled", True)
    background_tasks = BackgroundTasks()

    enqueue_auth_security_notification(
        background_tasks,
        user_id=7,
        event_name="Login detected",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    assert len(background_tasks.tasks) == 1
    task = background_tasks.tasks[0]
    assert task.func == send_auth_security_notification.delay
    assert task.kwargs == {
        "user_id": 7,
        "event_name": "Login detected",
        "ip": "127.0.0.1",
        "user_agent": "pytest",
    }
