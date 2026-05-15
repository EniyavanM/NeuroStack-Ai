"""Prometheus metrics hooks."""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "neurostack_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "neurostack_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


async def metrics_endpoint(_: Request) -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
