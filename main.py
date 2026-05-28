import os
from contextlib import asynccontextmanager
from redis.exceptions import ConnectionError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from api import api_router
from core.config import settings
from core.exception_handlers import register_exception_handlers
from core.logger import setup_logging
from core.metrics import metrics_middleware, metrics_response
from core.redis_client import close_cache_redis
from websocket.routes import router as ws_router
from websocket.service import RealtimeService

setup_logging()


@asynccontextmanager
async def lifespan(application: FastAPI):
    os.makedirs(settings.static.upload_dir, exist_ok=True)
    os.makedirs(settings.static.avatars_dir, exist_ok=True)

    realtime = RealtimeService(settings.websocket)
    application.state.realtime = realtime

    try:
        await realtime.start()
    except ConnectionError:
        logger.error("Не удалось подключиться к Redis, см. Traceback:")
        raise

    try:
        yield
    finally:
        await close_cache_redis()
        await realtime.stop()


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)
register_exception_handlers(app)

app.middleware("http")(metrics_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api.prefix)
app.include_router(ws_router)


@app.get("/")
def root():
    return {"message": "success"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return metrics_response()
