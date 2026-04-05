from __future__ import annotations

import logging


def _parse_status_code(value: object) -> int | None:
    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.isdigit():
        return int(value)

    return None


def _extract_access_path_and_status(record: logging.LogRecord) -> tuple[str | None, int | None]:
    if isinstance(record.args, tuple) and len(record.args) >= 5:
        return str(record.args[2]), _parse_status_code(record.args[4])

    request_line = record.__dict__.get("request_line")
    status_code = _parse_status_code(record.__dict__.get("status_code"))
    if not isinstance(request_line, str):
        return None, status_code

    parts = request_line.split(" ")
    if len(parts) < 2:
        return None, status_code

    return parts[1], status_code


class HealthAccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_path, status_code = _extract_access_path_and_status(record)
        if request_path is None or status_code is None:
            return True

        normalized_path = request_path.split("?", 1)[0]
        is_health_request = normalized_path.startswith("/health")
        is_successful_probe = 200 <= status_code < 300

        return not (is_health_request and is_successful_probe)