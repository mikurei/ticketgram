import logging
from functools import wraps
from typing import Callable

from consts import APPLICATION_NAME as APP_NAME
from prometheus_client import Counter, Summary, start_http_server

__logger = logging.getLogger(__name__)


CALLBACK_TOTAL = Counter(
    f"{APP_NAME}_callbacks_total",
    "Total amount of callbacks",
    ["func_name"],
)

CALLBACK_DURATION = Summary(
    f"{APP_NAME}_callback_duration_seconds",
    "Time spent processing callbacks",
    ["func_name"],
)


def monitor_callback(func: Callable):
    """
    A decorator which instruments the callback function with metrics.

    `ticketgram_callback_duration_seconds{func_name}`

    `ticketgram_callback_calls_total{func_name}`
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        name = func.__name__

        total_submetric = CALLBACK_TOTAL.labels(func_name=name)
        total_submetric.inc()

        duration_submetric = CALLBACK_DURATION.labels(func_name=name)
        with duration_submetric.time():
            return func(*args, **kwargs)

    return decorator


def run_exporter(port: int) -> None:
    """Starts Prometheus instance"""
    start_http_server(port)
    __logger.info(
        "Monitoring started, Prometheus Client listening on 0.0.0.0:%s", port
    )
