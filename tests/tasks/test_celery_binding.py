from core.config import settings
from tasks.outbox import process_outbox_events
from tasks.sessions import cleanup_user_sessions


def test_celery_tasks_are_bound_to_project_celery_app() -> None:
    expected_broker = settings.celery.broker_url

    assert cleanup_user_sessions.app.conf.broker_url == expected_broker
    assert process_outbox_events.app.conf.broker_url == expected_broker
