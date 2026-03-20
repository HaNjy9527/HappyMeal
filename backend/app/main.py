from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.consents import router as consent_router
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.core.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router)
app.include_router(profile_router)
app.include_router(consent_router)


@app.get("/")
def get_root() -> dict[str, str]:
    return {"message": settings.app_name}
