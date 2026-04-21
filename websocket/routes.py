from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    audience_raw = websocket.query_params.get("audience_id")
    audience_id: int | None = None

    if audience_raw:
        try:
            audience_id = int(audience_raw)
        except ValueError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid audience_id")
            return

    realtime = websocket.app.state.realtime
    connection_id = await realtime.connect(
        websocket,
        audience_id=audience_id,
        user_id=None,
        ip=websocket.client.host if websocket.client else None,
        user_agent=websocket.headers.get("user-agent"),
    )

    try:
        while True:
            await websocket.receive_text()
            await realtime.heartbeat(connection_id)
    except WebSocketDisconnect:
        await realtime.disconnect(connection_id)
    except Exception:
        await realtime.disconnect(connection_id)
        raise
