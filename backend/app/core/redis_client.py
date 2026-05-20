from __future__ import annotations

import logging

import redis

from app.core.config import get_settings


logger = logging.getLogger("app.redis")


def get_redis_client() -> redis.Redis | None:
    """
    回傳 Redis 連線物件。

    REDIS_URL 未設定或連線失敗時回傳 None，
    讓呼叫方靜默降級，不阻斷主流程。
    """
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.debug("Redis 連線失敗，降級跳過 cache: %s", exc)
        return None
