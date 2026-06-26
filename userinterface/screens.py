"""
1. Configure Jinja2
templates = Jinja2Templates(directory="userinterface/templates")
Permet à FastAPI de charger les fichiers HTML.

2. Désactive le cache
templates.env.cache = {}
Les modifications des templates HTML sont prises en compte immédiatement, sans redémarrer le serveur.

3. Création des constantes
MOIS_FR = [...]

"""

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