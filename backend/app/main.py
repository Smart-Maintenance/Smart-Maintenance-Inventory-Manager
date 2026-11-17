from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base

# Creează automat tabelele în SQLite la pornirea serverului
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartMIM API",
    description="API pentru managementul mentenanței și al stocurilor de piese",
    version="0.1.0"
)

# Permite conectarea aplicației Frontend (Rolul 2) fără erori CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "project": "SmartMIM Backend"}