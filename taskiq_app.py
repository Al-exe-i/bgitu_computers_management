from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq.serializers import JSONSerializer
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from core.config import TaskiqConfig, settings


def create_broker(config: TaskiqConfig, *, queue_name: str = "bgitu:tasks") -> RedisStreamBroker:
    return RedisStreamBroker(
        url=config.broker_url,
        queue_name=queue_name,
        consumer_id="0",
        xread_count=1,
        maxlen=10000,
    ).with_result_backend(
        RedisAsyncResultBackend(
            redis_url=config.result_backend,
            result_ex_time=config.result_ttl_seconds,
            prefix_str=f"{queue_name}:result",
            serializer=JSONSerializer(),
        )
    )


broker = create_broker(settings.taskiq)
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])
