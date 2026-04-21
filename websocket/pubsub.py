import asyncio
import json
from collections.abc import Awaitable, Callable

from loguru import logger
from redis.asyncio import Redis

from websocket.types import AudienceUpdatedEvent


class RedisEventBus:
    def __init__(
        self,
        *,
        redis_url: str,
        channel: str,
        reconnect_delay_seconds: int = 1,
        max_reconnect_delay_seconds: int = 10,
    ) -> None:
        self.channel = channel
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self.max_reconnect_delay_seconds = max_reconnect_delay_seconds
        self.publisher = Redis.from_url(redis_url, decode_responses=True)
        self.subscriber = Redis.from_url(redis_url, decode_responses=True)
        self._pubsub = None
        self._closed = False

    async def publish_audience_updated(self, audience_id: int) -> None:
        event = AudienceUpdatedEvent.new(audience_id)
        await self.publisher.publish(self.channel, json.dumps(event.to_payload()))

    async def run_forever(
        self,
        on_event: Callable[[AudienceUpdatedEvent], Awaitable[None]],
    ) -> None:
        backoff = self.reconnect_delay_seconds

        while not self._closed:
            try:
                self._pubsub = self.subscriber.pubsub(ignore_subscribe_messages=True)
                await self._pubsub.subscribe(self.channel)
                logger.info("Redis pubsub subscribed to {}", self.channel)
                backoff = self.reconnect_delay_seconds

                while not self._closed:
                    message = await self._pubsub.get_message(timeout=1.0)
                    if message is None or message.get("type") != "message":
                        continue

                    payload = json.loads(message["data"])
                    await on_event(AudienceUpdatedEvent.from_payload(payload))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Redis pubsub loop failed: {}", exc)
            finally:
                if self._pubsub is not None:
                    try:
                        await self._pubsub.aclose()
                    except Exception:
                        pass
                    self._pubsub = None

            if self._closed:
                break

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self.max_reconnect_delay_seconds)

    async def close(self) -> None:
        self._closed = True
        if self._pubsub is not None:
            try:
                await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None

        await self.publisher.aclose()
        await self.subscriber.aclose()
