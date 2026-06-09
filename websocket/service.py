import asyncio
import os
import socket
from datetime import datetime, timezone
from uuid import uuid4

from loguru import logger
from redis.asyncio import Redis

from core.config import WebSocketConfig
from websocket.manager import LocalConnectionManager, LocalConnectionState
from websocket.pubsub import RedisEventBus
from websocket.registry import RedisConnectionRegistry
from websocket.types import AudienceUpdatedEvent, RealtimeEvent, RealtimeNotificationEvent, RedisConnectionMeta


class RealtimeService:
    def __init__(self, config: WebSocketConfig) -> None:
        self.config = config
        self.manager = LocalConnectionManager()
        self.started_at = datetime.now(timezone.utc)
        self.instance_id = config.instance_id or self._make_instance_id()

        self.registry: RedisConnectionRegistry | None = None
        self.bus: RedisEventBus | None = None

        if self.config.enabled and self.config.transport == "redis":
            registry_redis = Redis.from_url(self.config.redis_url, decode_responses=True)
            self.registry = RedisConnectionRegistry(
                registry_redis,
                instance_ttl_seconds=self.config.instance_ttl_seconds,
                connection_ttl_seconds=self.config.connection_ttl_seconds,
            )
            self.bus = RedisEventBus(
                redis_url=self.config.redis_url,
                channel=self.config.pubsub_channel,
            )

        self._subscriber_task: asyncio.Task | None = None
        self._instance_heartbeat_task: asyncio.Task | None = None
        self._connections_heartbeat_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

    @staticmethod
    def _make_instance_id() -> str:
        return f"{socket.gethostname()}-{os.getpid()}-{uuid4().hex[:8]}"

    async def start(self) -> None:
        if not self.config.enabled:
            logger.info("Realtime service is disabled")
            return

        if self.registry is None or self.bus is None:
            logger.info("Realtime service started in {} mode", self.config.transport)
            return

        await self.registry.register_instance(
            self.instance_id,
            host=socket.gethostname(),
            pid=os.getpid(),
            started_at=self.started_at,
        )

        self._subscriber_task = asyncio.create_task(
            self.bus.run_forever(self.handle_event),
            name="realtime-redis-subscriber",
        )
        self._instance_heartbeat_task = asyncio.create_task(
            self._instance_heartbeat_loop(),
            name="realtime-instance-heartbeat",
        )
        self._connections_heartbeat_task = asyncio.create_task(
            self._connections_heartbeat_loop(),
            name="realtime-connections-heartbeat",
        )
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(),
            name="realtime-cleanup",
        )

        logger.info("Realtime service started in redis mode with instance_id={}", self.instance_id)

    async def stop(self) -> None:
        if not self.config.enabled:
            logger.info("Realtime service is disabled; stop skipped")
            return

        tasks = [
            self._subscriber_task,
            self._instance_heartbeat_task,
            self._connections_heartbeat_task,
            self._cleanup_task,
        ]

        for task in tasks:
            if task is not None:
                task.cancel()

        if tasks:
            await asyncio.gather(*(task for task in tasks if task is not None), return_exceptions=True)

        removed = await self.manager.close_all()
        for state in removed:
            await self._unregister_state(state)

        if self.registry is not None:
            await self.registry.unregister_instance(self.instance_id)
            await self.registry.close()

        if self.bus is not None:
            await self.bus.close()

        logger.info("Realtime service stopped for instance_id={}", self.instance_id)

    async def connect(
        self,
        connection,
        *,
        audience_id: int | None,
        user_id: int | None,
        ip: str | None,
        user_agent: str | None,
        client_id: str | None = None,
    ) -> str:
        if not self.config.enabled:
            raise RuntimeError("Realtime service is disabled")

        connection_id = str(uuid4())
        state, replaced = await self.manager.accept(
            connection_id=connection_id,
            connection=connection,
            audience_id=audience_id,
            user_id=user_id,
            client_id=client_id,
        )

        if replaced is not None:
            await self._unregister_state(replaced)
            try:
                await replaced.connection.close()
            except Exception:
                pass
            logger.debug(
                "Realtime client replaced: old_connection_id={} new_connection_id={} client_id={}",
                replaced.connection_id,
                connection_id,
                client_id,
            )

        if self.registry is not None:
            await self.registry.register_connection(
                self._build_meta(state, ip=ip, user_agent=user_agent)
            )

        logger.debug(
            "Realtime client connected: connection_id={} audience_id={} instance_id={}",
            connection_id,
            audience_id,
            self.instance_id,
        )
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        if not self.config.enabled:
            return

        state = await self.manager.remove(connection_id)
        if state is None:
            return

        await self._unregister_state(state)
        logger.debug("Realtime client disconnected: connection_id={}", connection_id)

    async def heartbeat(self, connection_id: str) -> None:
        if not self.config.enabled:
            return

        state = await self.manager.touch(connection_id)
        if state is None or self.registry is None:
            return

        await self.registry.touch_connection(
            connection_id,
            instance_id=self.instance_id,
            audience_key=self._build_meta(state, ip=None, user_agent=None).audience_key,
        )

    async def publish_audience_updated(self, audience_id: int) -> None:
        if not self.config.enabled:
            return

        if self.bus is not None:
            await self.bus.publish_audience_updated(audience_id)
            return

        await self.handle_event(AudienceUpdatedEvent.new(audience_id))

    async def publish_notification(self, *, user_id: int, payload: dict) -> None:
        if not self.config.enabled:
            return

        if self.bus is not None:
            await self.bus.publish_notification(user_id=user_id, payload=payload)
            return

        await self.handle_event(RealtimeNotificationEvent.new(user_id=user_id, payload=payload))

    async def handle_event(self, event: RealtimeEvent) -> None:
        if event.type == "audience_updated":
            await self._handle_audience_updated(event)
            return

        if event.type == "notification":
            await self._handle_notification(event)

    async def _handle_audience_updated(self, event: AudienceUpdatedEvent) -> None:
        dropped = await self.manager.broadcast_audience(
            event.audience_id,
            {"audience_updated": event.audience_id},
        )

        for state in dropped:
            await self._unregister_state(state)

    async def _handle_notification(self, event: RealtimeNotificationEvent) -> None:
        dropped = await self.manager.broadcast_user(
            event.user_id,
            {
                "type": "notification",
                "notification": event.payload,
            },
        )

        for state in dropped:
            await self._unregister_state(state)

    async def _instance_heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.config.heartbeat_interval_seconds)
            if self.registry is None:
                continue
            await self.registry.touch_instance(self.instance_id)

    async def _connections_heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.config.heartbeat_interval_seconds)
            if self.registry is None:
                continue

            states = await self.manager.snapshot()
            for state in states:
                await self.registry.touch_connection(
                    state.connection_id,
                    instance_id=self.instance_id,
                    audience_key=self._build_meta(state, ip=None, user_agent=None).audience_key,
                )

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(self.config.cleanup_interval_seconds)
            if self.registry is None:
                continue

            removed_connections = await self.registry.cleanup_expired_connections()
            removed_instances = await self.registry.cleanup_expired_instances()

            if removed_connections or removed_instances:
                logger.info(
                    "Redis realtime cleanup: connections_removed={} instances_removed={}",
                    removed_connections,
                    removed_instances,
                )

    def _build_meta(
        self,
        state: LocalConnectionState,
        *,
        ip: str | None,
        user_agent: str | None,
    ) -> RedisConnectionMeta:
        return RedisConnectionMeta(
            connection_id=state.connection_id,
            instance_id=self.instance_id,
            audience_id=state.audience_id,
            user_id=state.user_id,
            client_id=state.client_id,
            connected_at=state.connected_at,
            last_seen=state.last_seen,
            ip=ip,
            user_agent=user_agent,
        )

    async def _unregister_state(self, state: LocalConnectionState) -> None:
        if self.registry is None:
            return

        await self.registry.unregister_connection(
            state.connection_id,
            instance_id=self.instance_id,
            audience_key=self._build_meta(state, ip=None, user_agent=None).audience_key,
        )
