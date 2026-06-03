import asyncio
import json

from fastapi import APIRouter, HTTPException, Request, status
from starlette.responses import StreamingResponse

from dependencies.auth import user_dep

router = APIRouter()


class SSEConnection:
    def __init__(self, *, queue_size: int = 100) -> None:
        self._queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=queue_size)
        self._closed = False

    async def accept(self) -> None:
        return None

    async def send_json(self, payload: dict) -> None:
        if self._closed:
            raise RuntimeError("SSE connection is closed")

        try:
            self._queue.put_nowait(payload)
        except asyncio.QueueFull as exc:
            raise RuntimeError("SSE connection queue is full") from exc

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            self._queue.put_nowait(None)

    async def receive_json(self) -> dict | None:
        return await self._queue.get()


def _format_sse(payload: dict) -> str:
    event_name = payload.get("type") or ("audience_updated" if "audience_updated" in payload else "message")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_name}\ndata: {data}\n\n"


def _stream_response(event_stream):
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/events", include_in_schema=False)
async def sse_endpoint(request: Request):
    realtime = request.app.state.realtime
    if not realtime.config.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime events are disabled",
        )

    audience_raw = request.query_params.get("audience_id")
    audience_id: int | None = None

    if audience_raw:
        try:
            audience_id = int(audience_raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audience_id",
            ) from exc

    connection = SSEConnection()
    connection_id = await realtime.connect(
        connection,
        audience_id=audience_id,
        user_id=None,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    async def event_stream():
        try:
            yield "retry: 3000\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    payload = await asyncio.wait_for(
                        connection.receive_json(),
                        timeout=realtime.config.heartbeat_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    await realtime.heartbeat(connection_id)
                    yield ": ping\n\n"
                    continue

                if payload is None:
                    break

                await realtime.heartbeat(connection_id)
                yield _format_sse(payload)
        finally:
            await realtime.disconnect(connection_id)

    return _stream_response(event_stream)


@router.get("/events/notifications", include_in_schema=False)
async def notifications_sse_endpoint(request: Request, user: user_dep):
    realtime = request.app.state.realtime
    if not realtime.config.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Realtime events are disabled",
        )

    connection = SSEConnection()
    connection_id = await realtime.connect(
        connection,
        audience_id=None,
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    async def event_stream():
        try:
            yield "retry: 3000\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    payload = await asyncio.wait_for(
                        connection.receive_json(),
                        timeout=realtime.config.heartbeat_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    await realtime.heartbeat(connection_id)
                    yield ": ping\n\n"
                    continue

                if payload is None:
                    break

                await realtime.heartbeat(connection_id)
                yield _format_sse(payload)
        finally:
            await realtime.disconnect(connection_id)

    return _stream_response(event_stream)
