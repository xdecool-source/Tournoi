from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from api.routes import router
from contextlib import asynccontextmanager
from services.db import init_db_pool, init_db, init_archive_trigger, reaffectation_all
from fastapi.staticfiles import StaticFiles
from core.config import MOCK_FFTT, ENV, HELLOASSO_CARTE
from services.db import wake_db

import asyncio
import os

from dotenv import load_dotenv
load_dotenv()    
# si existe .env et pas de variable globale alors .env

@asynccontextmanager

async def lifespan(app: FastAPI):
    
    print("")
    print(" Application démarrage")
    print("")
    
    if MOCK_FFTT: {print( " Mode simulation licence : MOCK_FFTT = ", os.getenv("MOCK_FFTT"))}
    else: { print ( " Connexion FFTT : MOCK_FFTT = ", os.getenv("MOCK_FFTT"))}
    
    if ENV: {print( " On utilise Messagerie APi Brevo : ENV = ", os.getenv("ENV"))}
    else: { print ( " On utilise Messagerie SMTP Mail de Brevo : ENV = ", os.getenv("ENV"))}
    
    if HELLOASSO_CARTE: {print( " Paiement par carte avec helloAsso : HELLOASSO_CARTE = ", os.getenv("HELLOASSO_CARTE"))}
    else: { print ( " Pas de paiement avec HelloAsso : HELLOASSO_CARTE = ", os.getenv("HELLOASSO_CARTE"))}
    
    print("")
       
    await init_db_pool()
    await init_db()
    await init_archive_trigger()
    # promotion automatique des listes d'attente dans db.py se services
    await reaffectation_all()
    yield
    
    # arrêt propre
    print(" Application arrêt")

app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.mount("/static", StaticFiles(directory="userinterface"), name="static")

# Reveil Railway et Neon
@app.get("/ping")
async def ping():
    await wake_db()
    return {"status": "ok"}