import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from core.config import settings
from core.logger import setup_logging
from websocket.routes import router as ws_router
from websocket.service import RealtimeService

setup_logging()


@asynccontextmanager
async def lifespan(application: FastAPI):
    os.makedirs(settings.static.upload_dir, exist_ok=True)
    os.makedirs(settings.static.avatars_dir, exist_ok=True)

    realtime = RealtimeService(settings.websocket)
    application.state.realtime = realtime
    await realtime.start()

    try:
        yield
    finally:
        await realtime.stop()


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

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
