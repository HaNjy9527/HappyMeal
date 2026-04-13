from __future__ import annotations

from contextvars import ContextVar, Token
from uuid import uuid4


_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_path: ContextVar[str | None] = ContextVar("path", default=None)
_method: ContextVar[str | None] = ContextVar("method", default=None)
_client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)
_origin: ContextVar[str | None] = ContextVar("origin", default=None)
_referer: ContextVar[str | None] = ContextVar("referer", default=None)


def set_request_log_context(
    *,
    path: str,
    method: str,
    client_ip: str | None,
    user_agent: str | None,
    origin: str | None,
    referer: str | None,
) -> dict[str, Token[str | None]]:
    request_id = uuid4().hex
    return {
        "request_id": _request_id.set(request_id),
        "path": _path.set(path),
        "method": _method.set(method),
        "client_ip": _client_ip.set(client_ip),
        "user_agent": _user_agent.set(user_agent),
        "origin": _origin.set(origin),
        "referer": _referer.set(referer),
    }


def reset_request_log_context(tokens: dict[str, Token[str | None]]) -> None:
    _request_id.reset(tokens["request_id"])
    _path.reset(tokens["path"])
    _method.reset(tokens["method"])
    _client_ip.reset(tokens["client_ip"])
    _user_agent.reset(tokens["user_agent"])
    _origin.reset(tokens["origin"])
    _referer.reset(tokens["referer"])


def get_request_log_context() -> dict[str, str | None]:
    return {
        "request_id": _request_id.get(),
        "path": _path.get(),
        "method": _method.get(),
        "client_ip": _client_ip.get(),
        "user_agent": _user_agent.get(),
        "origin": _origin.get(),
        "referer": _referer.get(),
    }