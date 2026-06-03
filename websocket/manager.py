import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class RealtimeConnection(Protocol):
    async def accept(self) -> None: ...

    async def send_json(self, payload: dict) -> None: ...

    async def close(self) -> None: ...


@dataclass(slots=True)
class LocalConnectionState:
    connection_id: str
    connection: RealtimeConnection
    audience_id: int | None
    user_id: int | None
    connected_at: datetime
    last_seen: datetime


class LocalConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, LocalConnectionState] = {}
        self._audience_to_connections: dict[int | None, set[str]] = {}
        self._user_to_connections: dict[int, set[str]] = {}
        self._lock = asyncio.Lock()

    async def accept(
        self,
        *,
        connection_id: str,
        connection: RealtimeConnection,
        audience_id: int | None,
        user_id: int | None,
    ) -> LocalConnectionState:
        await connection.accept()

        now = datetime.now(timezone.utc)
        state = LocalConnectionState(
            connection_id=connection_id,
            connection=connection,
            audience_id=audience_id,
            user_id=user_id,
            connected_at=now,
            last_seen=now,
        )

        async with self._lock:
            self._connections[connection_id] = state
            self._audience_to_connections.setdefault(audience_id, set()).add(connection_id)
            if user_id is not None:
                self._user_to_connections.setdefault(user_id, set()).add(connection_id)

        return state

    async def remove(self, connection_id: str) -> LocalConnectionState | None:
        async with self._lock:
            state = self._connections.pop(connection_id, None)
            if state is None:
                return None

            audience_connections = self._audience_to_connections.get(state.audience_id)
            if audience_connections is not None:
                audience_connections.discard(connection_id)
                if not audience_connections:
                    self._audience_to_connections.pop(state.audience_id, None)

            if state.user_id is not None:
                user_connections = self._user_to_connections.get(state.user_id)
                if user_connections is not None:
                    user_connections.discard(connection_id)
                    if not user_connections:
                        self._user_to_connections.pop(state.user_id, None)

            return state

    async def touch(self, connection_id: str) -> LocalConnectionState | None:
        async with self._lock:
            state = self._connections.get(connection_id)
            if state is None:
                return None

            state.last_seen = datetime.now(timezone.utc)
            return state

    async def snapshot(self) -> list[LocalConnectionState]:
        async with self._lock:
            return list(self._connections.values())

    async def send_json(self, connection_id: str, payload: dict) -> LocalConnectionState | None:
        async with self._lock:
            state = self._connections.get(connection_id)

        if state is None:
            return None

        try:
            await state.connection.send_json(payload)
            return None
        except Exception:
            return await self.remove(connection_id)

    async def broadcast_audience(self, audience_id: int, payload: dict) -> list[LocalConnectionState]:
        async with self._lock:
            targets = set(self._audience_to_connections.get(None, set()))
            targets.update(self._audience_to_connections.get(audience_id, set()))

        dropped: list[LocalConnectionState] = []
        for connection_id in targets:
            removed = await self.send_json(connection_id, payload)
            if removed is not None:
                dropped.append(removed)

        return dropped

    async def broadcast_user(self, user_id: int, payload: dict) -> list[LocalConnectionState]:
        async with self._lock:
            targets = set(self._user_to_connections.get(user_id, set()))

        dropped: list[LocalConnectionState] = []
        for connection_id in targets:
            removed = await self.send_json(connection_id, payload)
            if removed is not None:
                dropped.append(removed)

        return dropped

    async def close_all(self) -> list[LocalConnectionState]:
        states = await self.snapshot()
        removed: list[LocalConnectionState] = []

        for state in states:
            popped = await self.remove(state.connection_id)
            if popped is None:
                continue

            try:
                await popped.connection.close()
            except Exception:
                pass

            removed.append(popped)

        return removed


ConnectionManager = LocalConnectionManager
