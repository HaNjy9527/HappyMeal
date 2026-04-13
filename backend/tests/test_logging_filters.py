import json
import logging

from app.core.logging_context import reset_request_log_context, set_request_log_context
from app.core.logging_filters import HealthAccessLogFilter, JsonFormatter, RequestContextFilter


def make_access_record(path: str, status_code: int) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:12345", "GET", path, "1.1", status_code),
        exc_info=None,
    )


def test_health_access_log_filter_suppresses_successful_health_probe():
    log_filter = HealthAccessLogFilter()

    assert log_filter.filter(make_access_record("/health", 200)) is False
    assert log_filter.filter(make_access_record("/health/db", 204)) is False


def test_health_access_log_filter_keeps_non_health_requests():
    log_filter = HealthAccessLogFilter()

    assert log_filter.filter(make_access_record("/profile", 200)) is True
    assert log_filter.filter(make_access_record("/analyses?limit=20", 200)) is True


def test_health_access_log_filter_keeps_unsuccessful_health_requests():
    log_filter = HealthAccessLogFilter()

    assert log_filter.filter(make_access_record("/health", 500)) is True
    assert log_filter.filter(make_access_record("/health/db", 503)) is True


def test_request_context_filter_injects_request_metadata():
    tokens = set_request_log_context(
        path="/auth/me",
        method="GET",
        client_ip="127.0.0.1",
        user_agent="pytest-agent",
        origin="https://app.example.com",
        referer="https://app.example.com/",
    )

    try:
        record = logging.LogRecord(
            name="app.auth",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="auth event",
            args=(),
            exc_info=None,
        )

        RequestContextFilter().filter(record)

        assert record.request_id
        assert record.path == "/auth/me"
        assert record.method == "GET"
        assert record.client_ip == "127.0.0.1"
        assert record.user_agent == "pytest-agent"
        assert record.origin == "https://app.example.com"
        assert record.referer == "https://app.example.com/"
    finally:
        reset_request_log_context(tokens)


def test_json_formatter_serializes_auth_fields():
    record = logging.LogRecord(
        name="app.auth",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="session created",
        args=(),
        exc_info=None,
    )
    record.event = "session_established"
    record.endpoint = "auth.exchange_token"
    record.outcome = "success"
    record.request_id = "req-123"
    record.user_id = "user-123"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["logger"] == "app.auth"
    assert payload["message"] == "session created"
    assert payload["event"] == "session_established"
    assert payload["endpoint"] == "auth.exchange_token"
    assert payload["outcome"] == "success"
    assert payload["request_id"] == "req-123"
    assert payload["user_id"] == "user-123"