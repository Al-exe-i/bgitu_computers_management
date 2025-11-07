# backend/app/websockets/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket import ConnectionManager

router = APIRouter()

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Можно обрабатывать входящие сообщения
    except WebSocketDisconnect:
        manager.disconnect(websocket)