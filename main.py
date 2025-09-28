from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.__init__ import api_router
from core.config import settings

app = FastAPI(debug=settings.DEBUG,)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Hello, FastAPI with JWT Auth!"}