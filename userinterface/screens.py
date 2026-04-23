# Appel les Templates et la date 

from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, date
from core.config import NOM_TOURNOI, DATE_TOURNOI

import os

templates = Jinja2Templates(directory="userinterface/templates")

#  désactive cache (clé du bug)

from dotenv import load_dotenv
load_dotenv()
templates.env.cache = {}

MOIS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]
def home_screen(request):
    date_obj = datetime.strptime(DATE_TOURNOI, "%d/%m/%Y")
    date_formatee = f"{date_obj.day} {MOIS_FR[date_obj.month]} {date_obj.year}"
    FROM_EMAIL=os.getenv("FROM_EMAIL")
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "DATE_TOURNOI": date_formatee,
            "NOM_TOURNOI": NOM_TOURNOI,
            "FROM_EMAIL": FROM_EMAIL
        }
    )