from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, equipment, inventory, tickets

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartMIM API",
    description="API pentru managementul mentenantei si al stocurilor de piese",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(equipment.router)
app.include_router(inventory.router)
app.include_router(tickets.router)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "online", "project": "SmartMIM Backend"}