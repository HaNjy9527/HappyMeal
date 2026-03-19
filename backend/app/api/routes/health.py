from fastapi import APIRouter

from app.db.session import can_connect_to_database


router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def get_database_health() -> dict[str, str]:
    is_connected = can_connect_to_database()

    return {"status": "ok" if is_connected else "degraded"}
