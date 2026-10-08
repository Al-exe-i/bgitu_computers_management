import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def services():
    compose = yaml.safe_load((ROOT / "docker-compose.yaml").read_text(encoding="utf-8"))
    return compose["services"]


def memory_bytes(value: str) -> int:
    match = re.fullmatch(r"(\d+)([kmgt])b?", value.lower())
    assert match is not None, value
    return int(match[1]) * 1024 ** ("kmgt".index(match[2]) + 1)


def test_frontend_restarts_after_failure(services):
    assert services["frontend"]["restart"] == "unless-stopped"


def test_redis_has_memory_headroom_without_evicting_tasks(services):
    redis = services["redis"]
    command = redis["command"]
    maximum = command[command.index("--maxmemory") + 1]
    policy = command[command.index("--maxmemory-policy") + 1]

    assert 0 < memory_bytes(maximum) <= memory_bytes(redis["mem_limit"]) // 2
    assert policy == "noeviction"
    assert redis["healthcheck"]["test"] == ["CMD", "redis-cli", "ping"]


def test_container_memory_budget_is_not_increased(services):
    assert memory_bytes(services["redis"]["mem_limit"]) <= 128 * 1024**2
    assert memory_bytes(services["redis"]["memswap_limit"]) <= 256 * 1024**2
    assert (
        sum(memory_bytes(service["mem_limit"]) for service in services.values())
        <= 1888 * 1024**2
    )


@pytest.mark.parametrize("name", ["backend", "taskiq_worker", "taskiq_scheduler"])
def test_redis_dependents_wait_for_readiness(services, name):
    assert services[name]["depends_on"]["redis"]["condition"] == "service_healthy"


def test_api_and_sse_use_dynamic_docker_dns():
    nginx = (ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "resolver 127.0.0.11 valid=5s ipv6=off;" in nginx
    assert "resolver_timeout 5s;" in nginx
    assert "set $backend_upstream backend:8000;" in nginx

    for location in ("/api/", "/events"):
        block = re.search(
            rf"location {re.escape(location)}\s*\{{(.*?)\}}", nginx, re.DOTALL
        )
        assert block is not None
        assert "proxy_pass http://$backend_upstream;" in block[1]
        assert "proxy_pass http://backend:8000;" not in block[1]

    events = re.search(r"location /events\s*\{(.*?)\}", nginx, re.DOTALL)[1]
    assert "proxy_buffering off;" in events
    assert "proxy_read_timeout 3600s;" in events
