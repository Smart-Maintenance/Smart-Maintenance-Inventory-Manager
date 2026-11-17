import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from . import models  # noqa: F401 - înregistrează tabelele înainte de create_all
from .database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="SmartMIM API",
    description="API pentru managementul mentenanței și al stocurilor de piese",
    version="0.1.0",
    lifespan=lifespan,
)

# Permite conectarea aplicației Frontend (Rolul 2) fără erori CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "project": "SmartMIM Backend"}


@app.get("/health/live", tags=["Health Check"])
def liveness():
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health Check"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ready"}
