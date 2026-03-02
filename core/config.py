import os
from dotenv import load_dotenv
load_dotenv()                 # mode production

TABLEAUX = {
    "T1": {"min": 500, "max": 799, "capacite": 48, "attente": 5},
    "T2": {"min": 500, "max": 999, "capacite": 48, "attente": 5},
    "T3": {"min": 500, "max": 1299, "capacite": 48, "attente": 5},
    "T4": {"min": 700, "max": 1599, "capacite": 48, "attente": 5},
    "T5": {"min": 800, "max": 1999, "capacite": 8, "attente": 2},
    "TS": {"min": None, "max": None,"capacite": 48, "attente": 5},
    "TH": {"min": None, "max": None,"capacite": 6, "attente": 4}
}

PRIX = {
    "T1": 8,
    "T2": 8,
    "T3": 8,
    "T4": 8,
    "T5": 9,
    "TS": 10,
    "TH": 9
}

######  Si chgt des ses parametres : Arret server et reload ceci pour le mode local ou distant FFTT
######  python -m uvicorn main:app --reload

# ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
MOCK_FFTT = os.getenv("MOCK_FFTT", "true").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
APP_ID = os.getenv("APP_ID", "")
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE", "")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")