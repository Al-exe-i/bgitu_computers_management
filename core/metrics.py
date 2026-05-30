import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Request, Response

HISTOGRAM_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def _label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(values: dict[str, str]) -> str:
    labels = ",".join(f'{key}="{_label_value(value)}"' for key, value in values.items())
    return f"{{{labels}}}"


@dataclass
class HttpMetricRow:
    count: int = 0
    duration_sum: float = 0.0
    buckets: dict[float, int] = field(default_factory=lambda: {bucket: 0 for bucket in HISTOGRAM_BUCKETS})


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._http: dict[tuple[str, str, str], HttpMetricRow] = defaultdict(HttpMetricRow)
        self._cache: dict[tuple[str, str, str], int] = defaultdict(int)

    def observe_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        key = (method, path, str(status_code))

        with self._lock:
            row = self._http[key]
            row.count += 1
            row.duration_sum += duration_seconds
            for bucket in HISTOGRAM_BUCKETS:
                if duration_seconds <= bucket:
                    row.buckets[bucket] += 1

    def observe_cache_event(
        self,
        *,
        cache: str,
        operation: str,
        result: str,
    ) -> None:
        key = (cache, operation, result)

        with self._lock:
            self._cache[key] += 1

    def render(self) -> str:
        lines = [
            "# HELP bgitu_app_info Application info.",
            "# TYPE bgitu_app_info gauge",
            'bgitu_app_info{app="bgitu_hardware_management"} 1',
            "# HELP bgitu_http_requests_total Total HTTP requests.",
            "# TYPE bgitu_http_requests_total counter",
        ]

        with self._lock:
            rows = list(self._http.items())
            cache_rows = list(self._cache.items())

        for (method, path, status_code), row in rows:
            labels = _labels({"method": method, "path": path, "status_code": status_code})
            lines.append(f"bgitu_http_requests_total{labels} {row.count}")

        lines.extend(
            [
                "# HELP bgitu_http_request_duration_seconds HTTP request duration in seconds.",
                "# TYPE bgitu_http_request_duration_seconds histogram",
            ]
        )

        for (method, path, status_code), row in rows:
            base_labels = {"method": method, "path": path, "status_code": status_code}
            for bucket in HISTOGRAM_BUCKETS:
                labels = _labels({**base_labels, "le": str(bucket)})
                lines.append(f"bgitu_http_request_duration_seconds_bucket{labels} {row.buckets[bucket]}")

            inf_labels = _labels({**base_labels, "le": "+Inf"})
            base = _labels(base_labels)
            lines.append(f"bgitu_http_request_duration_seconds_bucket{inf_labels} {row.count}")
            lines.append(f"bgitu_http_request_duration_seconds_count{base} {row.count}")
            lines.append(f"bgitu_http_request_duration_seconds_sum{base} {row.duration_sum:.9f}")

        lines.extend(
            [
                "# HELP bgitu_cache_events_total Total cache events.",
                "# TYPE bgitu_cache_events_total counter",
            ]
        )

        for (cache, operation, result), count in cache_rows:
            labels = _labels(
                {
                    "cache": cache,
                    "operation": operation,
                    "result": result,
                }
            )
            lines.append(f"bgitu_cache_events_total{labels} {count}")

        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()


async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - started_at
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        metrics_registry.observe_http_request(
            method=request.method,
            path=path,
            status_code=status_code,
            duration_seconds=duration,
        )


def metrics_response() -> Response:
    return Response(
        content=metrics_registry.render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
