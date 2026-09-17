"""FastAPI application entrypoint (UC-001, UC-002, UC-007)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.infrastructure.redis_client import close_redis, create_redis
from backend.infrastructure.redis_ledger_store import RedisLedgerStore
from backend.infrastructure.redis_session_store import RedisSessionStore
from backend.infrastructure.settings import get_settings
from backend.presentation.party_hub import PartyHub
from backend.presentation.sessions import router as sessions_router
from backend.presentation.statistics import router as statistics_router
from backend.presentation.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    redis = await create_redis(settings.redis_url)
    store = RedisSessionStore(redis)
    ledger = RedisLedgerStore(redis)
    await ledger.ensure()
    app.state.redis = redis
    app.state.settings = settings
    app.state.session_store = store
    app.state.ledger_store = ledger
    app.state.party_hub = PartyHub()
    try:
        yield
    finally:
        await close_redis(getattr(app.state, "redis", None))
        app.state.redis = None
        app.state.session_store = None
        app.state.ledger_store = None
        app.state.party_hub = None


def create_app() -> FastAPI:
    application = FastAPI(
        title="Sea Battle API",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(sessions_router)
    application.include_router(statistics_router)
    application.include_router(ws_router)
    return application


app = create_app()
