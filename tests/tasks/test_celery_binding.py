from core.config import settings
from tasks.notifications import (
    send_auth_security_notification,
    send_hardware_state_notification,
)
from tasks.sessions import cleanup_user_sessions


def test_celery_tasks_are_bound_to_project_celery_app() -> None:
    expected_broker = settings.celery.broker_url

    assert cleanup_user_sessions.app.conf.broker_url == expected_broker
    assert send_hardware_state_notification.app.conf.broker_url == expected_broker
    assert send_auth_security_notification.app.conf.broker_url == expected_broker
