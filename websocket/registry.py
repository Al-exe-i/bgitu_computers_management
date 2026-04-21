from datetime import datetime, timezone

from redis.asyncio import Redis

from websocket.types import RedisConnectionMeta


class RedisConnectionRegistry:
    def __init__(
        self,
        redis: Redis,
        *,
        instance_ttl_seconds: int,
        connection_ttl_seconds: int,
        prefix: str = "ws",
    ) -> None:
        self.redis = redis
        self.instance_ttl_seconds = instance_ttl_seconds
        self.connection_ttl_seconds = connection_ttl_seconds
        self.prefix = prefix

    def _instances_key(self) -> str:
        return f"{self.prefix}:instances"

    def _connections_key(self) -> str:
        return f"{self.prefix}:connections"

    def _instance_key(self, instance_id: str) -> str:
        return f"{self.prefix}:instance:{instance_id}"

    def _instance_connections_key(self, instance_id: str) -> str:
        return f"{self.prefix}:instance:{instance_id}:connections"

    def _connection_key(self, connection_id: str) -> str:
        return f"{self.prefix}:connection:{connection_id}"

    def _audience_connections_key(self, audience_key: str) -> str:
        return f"{self.prefix}:audience:{audience_key}:connections"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _score_for(now: datetime, ttl_seconds: int) -> float:
        return now.timestamp() + ttl_seconds

    async def register_instance(
        self,
        instance_id: str,
        *,
        host: str,
        pid: int,
        started_at: datetime,
    ) -> None:
        now = self._now()
        expire_at = self._score_for(now, self.instance_ttl_seconds)
        mapping = {
            "instance_id": instance_id,
            "host": host,
            "pid": str(pid),
            "started_at": started_at.isoformat(),
            "last_seen": now.isoformat(),
        }

        pipeline = self.redis.pipeline()
        await pipeline.zadd(self._instances_key(), {instance_id: expire_at})
        pipeline.hset(self._instance_key(instance_id), mapping=mapping)
        await pipeline.execute()

    async def touch_instance(self, instance_id: str) -> None:
        now = self._now()
        expire_at = self._score_for(now, self.instance_ttl_seconds)

        pipeline = self.redis.pipeline()
        await pipeline.zadd(self._instances_key(), {instance_id: expire_at})
        pipeline.hset(self._instance_key(instance_id), mapping={"last_seen": now.isoformat()})
        await pipeline.execute()

    async def unregister_instance(self, instance_id: str) -> None:
        pipeline = self.redis.pipeline()
        await pipeline.zrem(self._instances_key(), instance_id)
        await pipeline.delete(self._instance_key(instance_id))
        await pipeline.delete(self._instance_connections_key(instance_id))
        await pipeline.execute()

    async def register_connection(self, meta: RedisConnectionMeta) -> None:
        expire_at = self._score_for(meta.last_seen, self.connection_ttl_seconds)

        pipeline = self.redis.pipeline()
        await pipeline.zadd(self._connections_key(), {meta.connection_id: expire_at})
        await pipeline.zadd(self._instance_connections_key(meta.instance_id), {meta.connection_id: expire_at})
        await pipeline.zadd(self._audience_connections_key(meta.audience_key), {meta.connection_id: expire_at})
        pipeline.hset(self._connection_key(meta.connection_id), mapping=meta.to_mapping())
        await pipeline.execute()

    async def touch_connection(
        self,
        connection_id: str,
        *,
        instance_id: str,
        audience_key: str,
    ) -> None:
        now = self._now()
        expire_at = self._score_for(now, self.connection_ttl_seconds)

        pipeline = self.redis.pipeline()
        await pipeline.zadd(self._connections_key(), {connection_id: expire_at})
        await  pipeline.zadd(self._instance_connections_key(instance_id), {connection_id: expire_at})
        await pipeline.zadd(self._audience_connections_key(audience_key), {connection_id: expire_at})
        pipeline.hset(self._connection_key(connection_id), mapping={"last_seen": now.isoformat()})
        await pipeline.execute()

    async def unregister_connection(
        self,
        connection_id: str,
        *,
        instance_id: str,
        audience_key: str,
    ) -> None:
        pipeline = self.redis.pipeline()
        await pipeline.zrem(self._connections_key(), connection_id)
        await pipeline.zrem(self._instance_connections_key(instance_id), connection_id)
        await pipeline.zrem(self._audience_connections_key(audience_key), connection_id)
        await pipeline.delete(self._connection_key(connection_id))
        await pipeline.execute()

    async def cleanup_expired_connections(self, *, batch_size: int = 500) -> int:
        now_ts = self._now().timestamp()
        expired_ids = await self.redis.zrangebyscore(self._connections_key(), min="-inf", max=now_ts, start=0, num=batch_size)
        if not expired_ids:
            return 0

        pipeline = self.redis.pipeline()
        for connection_id in expired_ids:
            raw_meta = await self.redis.hgetall(self._connection_key(connection_id))
            meta = RedisConnectionMeta.from_mapping(raw_meta) if raw_meta else None

            await pipeline.zrem(self._connections_key(), connection_id)
            if meta is not None:
                await pipeline.zrem(self._instance_connections_key(meta.instance_id), connection_id)
                await pipeline.zrem(self._audience_connections_key(meta.audience_key), connection_id)
            await pipeline.delete(self._connection_key(connection_id))

        await pipeline.execute()
        return len(expired_ids)

    async def cleanup_expired_instances(self, *, batch_size: int = 100) -> int:
        now_ts = self._now().timestamp()
        expired_ids = await self.redis.zrangebyscore(self._instances_key(), min="-inf", max=now_ts, start=0, num=batch_size)
        if not expired_ids:
            return 0

        pipeline = self.redis.pipeline()
        for instance_id in expired_ids:
            await pipeline.zrem(self._instances_key(), instance_id)
            await pipeline.delete(self._instance_key(instance_id))
            await pipeline.delete(self._instance_connections_key(instance_id))

        await pipeline.execute()
        return len(expired_ids)

    async def close(self) -> None:
        await self.redis.aclose()
