# Config de L"Appli : Parametres
######  Si chgt des ses parametres : Arret server et reload ceci pour le mode local ou distant FFTT
######  python -m uvicorn main:app --reload

import os
from dotenv import load_dotenv
load_dotenv()    # si existe .env et pas de variable globale alors .env

MOCK_FFTT = os.getenv("MOCK_FFTT", "true").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
APP_ID = os.getenv("APP_ID", "")
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE", "")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_TOURNOI = "28/03/2027"
NOM_TOURNOI = "Homopongistus"

TABLEAUX = {
    "T1": {"min": 500, "max": 799, "capacite": 8, "attente": 2},
    "T2": {"min": 500, "max": 999, "capacite": 8, "attente": 2},
    "T3": {"min": 500, "max": 1299, "capacite": 8, "attente": 2},
    "T4": {"min": 700, "max": 1599, "capacite": 8, "attente": 2},
    "T5": {"min": 800, "max": 1999, "capacite": 8, "attente": 2},
    "TS": {"min": None, "max": None, "label": "Toutes Séries", "capacite": 8, "attente": 2},
    "TH": {"min": None, "max": None, "label": "Handicap", "capacite": 8, "attente": 2},
    "T6": {"min": 800, "max": 1999, "capacite": 8, "attente": 2}
}

PRIX = {
    "T1": 8,
    "T2": 8,
    "T3": 8,
    "T4": 8,
    "T5": 9,
    "TS": 10,
    "TH": 9,
    "T6": 10
}

