from fastapi import BackgroundTasks
from websocket.routes import manager

def broadcast_audience_updated(background_tasks: BackgroundTasks, audience_id: int) -> None:
    background_tasks.add_task(manager.broadcast, {"audience_updated": audience_id})