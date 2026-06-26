"""
Config de L"Appli : Parametres
  Si chgt des ses parametres : Arret server et reload ceci pour le mode local ou distant FFTT
  python -m uvicorn main:app --reload
"T7": {"min": 500, "max": 1999, "capacite": 8, "attente": 2, "prix": 8, "jour": {
        "id": 2,
        "label": "Lundi"
    }},
"id": 1 = Dimanche "id": 2 = lundi etc
"""

import os
from dotenv import load_dotenv
load_dotenv()    # si existe .env et pas de variable globale alors .env

MOCK_FFTT = os.getenv("MOCK_FFTT", "true").lower() == "true"
ENV = os.getenv("ENV", "prod").lower() == "prod"
HELLOASSO_CARTE= os.getenv("HELLOASSO_CARTE", "true").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "")
APP_ID = os.getenv("APP_ID", "")
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE", "")
ADMIN_PASS_HASH = os.getenv("ADMIN_PASS_HASH")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABLEAUX = {
    "T1": {"min": 500, "max": 799,"label": "T 500-799", "capacite": 48,
        "attente": 3, "prix": 8, "jour": 
        { "id": 1,
        "label": "Dimanche",
        "hour": "11h00"
        }
        },
    "T2": {"min": 500, "max": 999,"label": "T 500-999", "capacite": 48,
        "attente": 3, "prix": 8, "jour": 
        {"id": 1,
        "label": "Dimanche",
        "hour": "8h30"
        }
        },
    "T3": {"min": 500, "max": 1299,"label": "T 500-1299", "capacite": 48,
        "attente": 3, "prix": 8, "jour": 
        {"id": 1,
        "label": "Dimanche",
        "hour": "14h30"
        }
        },
    "T4": {"min": 700, "max": 1599,"label": "T 700-1599", "capacite": 48,
        "attente": 3, "prix": 8, "jour": 
        {"id": 1,
        "label": "Dimanche",
        "hour": "9h45"
        }
        },
    "T5": {"min": 800, "max": 1999, "label": "T 800-1999", "capacite": 48,
        "attente": 3, "prix": 9, "jour":
        {"id": 1,
        "label": "Dimanche",
        "hour": "12h00"
        }
        },
    "TS": {"min": None, "max": None, "label": "Toutes Séries", "capacite": 50,
        "attente": 5, "prix": 10, "jour": 
        {"id": 1,
        "label": "Dimanche",
        "hour": "13h00"
        }
        },
    "TH": {"min": None, "max": None, "label": "Handicap", "capacite": 48,
        "attente": 5, "prix": 9, "jour": 
        {"id": 1,
        "label": "Dimanche",
        "hour": "14h00"
        }
        },
    
}

