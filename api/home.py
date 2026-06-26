"""
Affiche la page d'accueil et fournit la configuration utilisée par le front-end.
GET "/", response_class=HTMLResponse
GET /config
GET /tableaux

"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.config import TABLEAUX
from datetime import datetime
from userinterface.screens import MOIS_FR

import os

router = APIRouter()

templates = Jinja2Templates(
    directory="userinterface/templates"
)

FROM_EMAIL = os.getenv("FROM_EMAIL")
ORIGINE_EMAIL = os.getenv("ORIGINE_EMAIL")
NBRE_TABLEAU = os.getenv("NBRE_TABLEAU")
DATE_TOURNOI = os.getenv("DATE_TOURNOI")
DATE_TOURNOI_JOUR = os.getenv("DATE_TOURNOI_JOUR")
NOM_TOURNOI = os.getenv("NOM_TOURNOI")
HELLOASSO_CARTE = (os.getenv("HELLOASSO_CARTE", "true").lower() == "true")

# Page d'accueil

@router.get("/", response_class=HTMLResponse)

async def home(request: Request):
    date_obj = datetime.strptime(
        DATE_TOURNOI,
        "%d/%m/%Y"
    )
    date_formatee = (
        f"{date_obj.day} "
        f"{MOIS_FR[date_obj.month]} "
        f"{date_obj.year}"
    )
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "NBRE_TABLEAU": NBRE_TABLEAU,
            "DATE_TOURNOI": date_formatee,
            "DATE_TOURNOI_JOUR": DATE_TOURNOI_JOUR,
            "NOM_TOURNOI": NOM_TOURNOI,
            "FROM_EMAIL": FROM_EMAIL,
            "ORIGINE_EMAIL": ORIGINE_EMAIL,
        },
    )

# Configuration Front

@router.get("/config")

async def get_config():
    return {
        "helloasso_carte": HELLOASSO_CARTE
    }

# Tableaux

@router.get("/tableaux")

async def get_tableaux():
    result = {}
    for key, conf in TABLEAUX.items():
        result[key] = {
            **conf,
            "prix": conf.get("prix", 0)
        }
    return result