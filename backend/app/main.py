from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.analyses import router as analysis_router
from app.api.routes.consents import router as consent_router
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.core.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.analysis_upload_path).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key or "dev-session-secret",
    session_cookie="happymeal_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=settings.app_env == "production",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(consent_router)
app.include_router(analysis_router)


@app.get("/")
def get_root() -> dict[str, str]:
    return {"message": settings.app_name}
