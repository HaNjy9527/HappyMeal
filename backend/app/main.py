from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.analyses import router as analysis_router
from app.api.routes.consents import router as consent_router
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.core.config import get_settings
from app.core.logging_context import get_request_log_context, reset_request_log_context, set_request_log_context


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.analysis_upload_path).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
is_production = settings.app_env == "production"
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key or "dev-session-secret",
    session_cookie="happymeal_session",
    max_age=60 * 60 * 24 * 7,
    same_site="none" if is_production else "lax",
    https_only=is_production,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def attach_request_log_context(request: Request, call_next):
    tokens = set_request_log_context(
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        origin=request.headers.get("origin"),
        referer=request.headers.get("referer"),
    )

    try:
        response = await call_next(request)
        request_id = get_request_log_context().get("request_id")
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response
    finally:
        reset_request_log_context(tokens)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(consent_router)
app.include_router(analysis_router)


@app.get("/")
def get_root() -> dict[str, str]:
    return {"message": settings.app_name}
