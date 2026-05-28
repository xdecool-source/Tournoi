# Appel les Templates et la date 
# configuration templates + constantes user interface

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

templates = Jinja2Templates(directory="userinterface/templates")

#  désactive cache (clé du bug)

load_dotenv()
# désactive cache Jinja
templates.env.cache = {}

MOIS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]