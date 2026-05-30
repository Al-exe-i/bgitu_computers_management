from core.metrics import MetricsRegistry


def test_metrics_registry_renders_prometheus_http_metrics() -> None:
    registry = MetricsRegistry()

    registry.observe_http_request(
        method="GET",
        path="/api/v1/audiences/{audience_id}",
        status_code=200,
        duration_seconds=0.02,
    )

    output = registry.render()

    assert "# TYPE bgitu_http_requests_total counter" in output
    assert (
        'bgitu_http_requests_total{method="GET",path="/api/v1/audiences/{audience_id}",status_code="200"} 1'
        in output
    )
    assert "bgitu_http_request_duration_seconds_bucket" in output
    assert "bgitu_http_request_duration_seconds_count" in output
    assert "bgitu_http_request_duration_seconds_sum" in output


def test_metrics_registry_renders_prometheus_cache_metrics() -> None:
    registry = MetricsRegistry()

    registry.observe_cache_event(
        cache="identity_user",
        operation="get",
        result="hit",
    )
    registry.observe_cache_event(
        cache="identity_user",
        operation="get",
        result="hit",
    )
    registry.observe_cache_event(
        cache="identity_user",
        operation="get",
        result="miss",
    )

    output = registry.render()

    assert "# TYPE bgitu_cache_events_total counter" in output
    assert 'bgitu_cache_events_total{cache="identity_user",operation="get",result="hit"} 2' in output
    assert 'bgitu_cache_events_total{cache="identity_user",operation="get",result="miss"} 1' in output
