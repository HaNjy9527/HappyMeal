from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.core.logging_context import get_request_log_context


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


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_context = get_request_log_context()
        for key, value in request_context.items():
            if key in record.__dict__:
                continue
            record.__dict__[key] = value

        return True


class JsonFormatter(logging.Formatter):
    _optional_fields = (
        "request_id",
        "path",
        "method",
        "client_ip",
        "user_agent",
        "origin",
        "referer",
        "event",
        "endpoint",
        "outcome",
        "reason",
        "status_code",
        "user_id",
        "line_user_id_hash",
        "has_code",
        "has_state",
        "has_error",
        "is_new_user",
        "fallback_used",
        "expected_state_present",
        "redirect_target",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in self._optional_fields:
            value = record.__dict__.get(field)
            if value is None or value == "":
                continue
            payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)