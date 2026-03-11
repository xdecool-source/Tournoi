from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from api.routes import router
from contextlib import asynccontextmanager
from services.db import init_db_pool, init_db
from services.scheduler import export_scheduler
from fastapi.staticfiles import StaticFiles

import asyncio

@asynccontextmanager

async def lifespan(app: FastAPI):

    print("🚀 Application démarrage")
    await init_db_pool()
    await init_db()
    # lancement du scheduler
    task = asyncio.create_task(export_scheduler())
    print("⏰ Scheduler démarré")
    yield
    # arrêt propre
    task.cancel()
    print("🛑 Application arrêt")


app = FastAPI(lifespan=lifespan)
app.include_router(router)
templates = Jinja2Templates(directory="userinterface/templates")
app.mount("/static", StaticFiles(directory="userinterface"), name="static")

@app.get("/ping")

async def ping():
    return {"status": "ok"}