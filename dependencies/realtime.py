from typing import Annotated

from fastapi import Depends, Request

from websocket.service import RealtimeService


def get_realtime(request: Request) -> RealtimeService:
    return request.app.state.realtime


realtime_dep = Annotated[RealtimeService, Depends(get_realtime)]
