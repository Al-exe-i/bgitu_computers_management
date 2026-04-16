from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
from core.config import settings
import os
from core.logger import setup_logging
from websocket.routes import router as ws_router

setup_logging()
app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
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

os.makedirs(settings.static.upload_dir, exist_ok=True)
os.makedirs(settings.static.avatars_dir, exist_ok=True)


@app.get("/")
def root():
    return {"message": "success"}
