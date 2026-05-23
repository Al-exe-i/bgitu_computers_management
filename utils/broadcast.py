from fastapi import BackgroundTasks

from websocket.service import RealtimeService


async def publish_audience_updated(
    realtime: RealtimeService,
    audience_id: int,
) -> None:
    if not realtime.config.enabled:
        return

    await realtime.publish_audience_updated(audience_id)


def broadcast_audience_updated(
    background_tasks: BackgroundTasks,
    realtime: RealtimeService,
    audience_id: int,
) -> None:
    background_tasks.add_task(publish_audience_updated, realtime, audience_id)
