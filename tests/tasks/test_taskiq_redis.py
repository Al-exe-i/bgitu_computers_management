"""Opt-in Redis transport check; touches only unique test keys, never application DB."""

import asyncio
import os
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from taskiq.receiver import Receiver

from core.config import TaskiqConfig
from taskiq_app import create_broker
from tasks import sessions


@pytest.mark.skipif(
    not os.getenv("TEST_TASKIQ_REDIS_URL"),
    reason="Set TEST_TASKIQ_REDIS_URL to run Redis integration",
)
def test_delivery_before_worker_start_result_and_acknowledgement(monkeypatch):
    calls = []

    async def cleanup(retention_days):
        calls.append(retention_days)
        if retention_days == 0:
            raise RuntimeError("test database failure")
        return {
            "expired_deleted": 2,
            "revoked_deleted": 1,
            "retention_days": retention_days,
        }

    monkeypatch.setattr(sessions, "_cleanup_user_sessions_async", cleanup)

    async def check():
        url = os.environ["TEST_TASKIQ_REDIS_URL"]
        queue = f"test:taskiq:{uuid4().hex}"
        broker = create_broker(
            TaskiqConfig(broker_url=url, result_backend=url), queue_name=queue
        )
        task = broker.task(task_name="test.cleanup")(
            sessions.cleanup_user_sessions.original_func
        )
        redis = Redis.from_url(url)
        listener = None
        try:
            # Sending before startup must not be skipped when the group is created.
            sent = await task.kiq(7)
            await broker.startup()
            receiver = Receiver(broker, max_async_tasks=1)
            listener = broker.listen()
            message = await asyncio.wait_for(anext(listener), timeout=5)
            await receiver.callback(message, raise_err=True)
            result = await sent.wait_result(timeout=5)
            assert not result.is_err
            assert result.return_value["expired_deleted"] == 2
            assert calls == [7]
            assert (await redis.xpending(queue, broker.consumer_group_name))[
                "pending"
            ] == 0
            assert 0 < await redis.ttl(f"{queue}:result:{sent.task_id}") <= 86400

            failed = await task.kiq(0)
            message = await asyncio.wait_for(anext(listener), timeout=5)
            await receiver.callback(message, raise_err=True)
            result = await failed.wait_result(timeout=5)
            assert result.is_err
            assert str(result.error) == "test database failure"
            assert (await redis.xpending(queue, broker.consumer_group_name))[
                "pending"
            ] == 0
        finally:
            if listener is not None:
                await listener.aclose()
            keys = [key async for key in redis.scan_iter(match=f"{queue}*")]
            if keys:
                await redis.delete(*keys)
            await redis.aclose()
            await broker.shutdown()

    asyncio.run(check())
