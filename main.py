from fastapi import FastAPI
from api.routes import router
from services.db import init_db_pool, init_db
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

print("APP ID =", id(app))
app.include_router(router)
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

@app.get("/ping")
async def ping():
    return {"status": "ok"}
