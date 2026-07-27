"""
démarre l'application, initialise la base  et affiche la configuration.
Création de  l'application FastAPI, 
enregistre les routes, les fichiers statiques
GET (/ping) pour railway et neon

"""

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from services.db import init_db_pool, init_db, init_archive_trigger, reaffectation_all
from fastapi.staticfiles import StaticFiles
from core.config import MOCK_FFTT, ENV, HELLOASSO_CARTE, ENVCODE
from services.db import wake_db

import asyncio
import os

from dotenv import load_dotenv
load_dotenv()    
# si existe .env et pas de variable globale alors .env

@asynccontextmanager

async def lifespan(app: FastAPI):
    
    print("")
    print(" 🟢 Gestion Tournoi : Startup")
    print("")
    
    if MOCK_FFTT: {print( " Mode simulation licence : MOCK_FFTT = ", os.getenv("MOCK_FFTT"))}
    else: { print ( " Connexion FFTT : MOCK_FFTT = ", os.getenv("MOCK_FFTT"))}
    
    if HELLOASSO_CARTE: {print( " Paiement par carte avec helloAsso Impossible en local car mode HTTP : HELLOASSO_CARTE = ", os.getenv("HELLOASSO_CARTE"))}
    else: { print ( " Pas de paiement avec HelloAsso : HELLOASSO_CARTE = ", os.getenv("HELLOASSO_CARTE"))}
    
    if ENV: {print( " On utilise Messagerie APi Brevo : ENV = ", os.getenv("ENV"))}
    else: { print ( " On utilise Messagerie SMTP Mail de Brevo : ENV = ", os.getenv("ENV"))}
    
    if ENVCODE: {print( " Bypass validation code = ", os.getenv("ENVCODE"))}
    else: { print ( " On utilise la Validation du code = ", os.getenv("ENVCODE"))}
    
    print("")
       
    await init_db_pool()
    await init_db()
    await init_archive_trigger()
    # promotion automatique des listes d'attente dans db.py se services
    await reaffectation_all()
    yield
    
    # arrêt propre
    print(" 🔴 Application arrêt")

app = FastAPI(lifespan=lifespan)

from api import (
    home,
    licence,
    inscription,
    admin,
    export,
    verification,
    helloasso,
)

app.include_router(home.router)
app.include_router(licence.router)
app.include_router(inscription.router)
app.include_router(admin.router)
app.include_router(export.router)
app.include_router(verification.router)
app.include_router(helloasso.router)
app.mount("/static", StaticFiles(directory="userinterface"), name="static")

# Reveil Railway et Neon
@app.get("/ping")
async def ping():
    await wake_db()
    return {"status": "ok"}