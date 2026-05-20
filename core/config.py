# Config de L"Appli : Parametres
######  Si chgt des ses parametres : Arret server et reload ceci pour le mode local ou distant FFTT
######  python -m uvicorn main:app --reload
# "T7": {"min": 500, "max": 1999, "capacite": 8, "attente": 2, "prix": 8, "jour": {
#         "id": 2,
#         "label": "Lundi"
#     }},
# "id": 1 = Dimanche "id": 2 = lundi

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
DATE_TOURNOI_JOUR = "Dimanche"
NOM_TOURNOI = "Homopongistus"

TABLEAUX = {
    "T1": {"min": 500, "max": 799, "capacite": 10, "attente": 2, "prix": 8, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "T2": {"min": 500, "max": 999, "capacite": 10, "attente": 2, "prix": 8, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "T3": {"min": 500, "max": 1299, "capacite": 10, "attente": 2, "prix": 8, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "T4": {"min": 700, "max": 1599, "capacite": 10, "attente": 2, "prix": 8, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "T5": {"min": 800, "max": 1999, "capacite": 10, "attente": 2, "prix": 9, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "TS": {"min": None, "max": None, "label": "Toutes Séries", "capacite": 15, "attente": 13, "prix": 10, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    "TH": {"min": None, "max": None, "label": "Handicap", "capacite": 15, "attente": 5, "prix": 9, "jour": {
        "id": 1,
        "label": "Dimanche"
    }},
    
}

