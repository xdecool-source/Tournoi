from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from api.routes import router
from contextlib import asynccontextmanager
from services.db import init_db_pool, init_db
from fastapi.staticfiles import StaticFiles

import asyncio
import os

from dotenv import load_dotenv
load_dotenv()    
# si existe .env et pas de variable globale alors .env

@asynccontextmanager

async def lifespan(app: FastAPI):
    
    print(" Application démarrage")
    print(" Imitation FFTT : MOCK_FFTT raw =", os.getenv("MOCK_FFTT"))

    await init_db_pool()
    await init_db()
    yield
    
    # arrêt propre
    print(" Application arrêt")

app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.mount("/static", StaticFiles(directory="userinterface"), name="static")

@app.get("/ping")

async def ping():
    return {"status": "ok"}