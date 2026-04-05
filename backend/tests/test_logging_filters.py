import logging

from app.core.logging_filters import HealthAccessLogFilter


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