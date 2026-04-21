from fastapi import BackgroundTasks

from websocket.service import RealtimeService


def broadcast_audience_updated(
    background_tasks: BackgroundTasks,
    realtime: RealtimeService,
    audience_id: int,
) -> None:
    background_tasks.add_task(realtime.publish_audience_updated, audience_id)
