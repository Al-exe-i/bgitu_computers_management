from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
from core.config import settings
import os
from websocket.routes import router as ws_router

app = FastAPI(debug=settings.DEBUG, default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api.prefix)
app.include_router(ws_router)

os.makedirs(settings.static.upload_dir, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Hello, FastAPI with JWT Auth!"}
