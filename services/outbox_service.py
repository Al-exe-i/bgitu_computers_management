from celery_app import celery_app
from db.post_commit import add_post_commit_hook
from repositories.outbox_event_repo import OutboxEventRepository


OUTBOX_PROCESS_TASK = "tasks.outbox.process_outbox_events"
_OUTBOX_NUDGE_REGISTERED_KEY = "outbox_nudge_registered"


class OutboxPublisher:
    def __init__(self, repo: OutboxEventRepository) -> None:
        self.repo = repo

    async def publish(self, *, event_type: str, payload: dict) -> None:
        await self.repo.create(event_type=event_type, payload=payload)
        self._register_processing_nudge()

    def _register_processing_nudge(self) -> None:
        session = self.repo.db
        if session.info.get(_OUTBOX_NUDGE_REGISTERED_KEY):
            return

        session.info[_OUTBOX_NUDGE_REGISTERED_KEY] = True
        add_post_commit_hook(
            session,
            lambda: celery_app.send_task(OUTBOX_PROCESS_TASK),
        )
