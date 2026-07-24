"""
Envoie un code de vérification par email et vérifie ce code avant l'inscription.
POST /send-code
POST /verify-code
POST /check-liste-password

"""

import os

from fastapi import APIRouter, BackgroundTasks
from services.mail_code import (
    send_email,
    store_verification_code,
    verify_code,
)

router = APIRouter()

ENVCODE = os.getenv("ENVCODE", "dev")
INSCRIT_PASS = os.getenv("INSCRIT_PASS")

# Envoi du code de vérification

@router.post("/send-code")

async def send_code(
    data: dict,
    background_tasks: BackgroundTasks
):
    email = data["email"].strip().lower()
    try:
        code = store_verification_code(email)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }

    html = f"""
    <h2>
        Voici votre code de vérification 
        pour valider votre connexion
        <h1>{code}</h1>
    </h2>
    <p>
        Ce code expire dans 5 minutes.
    </p>
    <p>
        Une fois votre inscription validée
        et avec ce mot de passe <b>{INSCRIT_PASS}</b>
        vous pourrez consulter la liste
        des joueurs inscrits :
    </p>
    <p> 
        Pour cela relancer l'application Inscription et saissez votre licence
        puis cliquer sur "Liste des inscrits" en bas à droite
    </p>
    <p>
        Si vous n'êtes pas à l'origine
        de cette demande,
        ignorez simplement cet email.
    </p>
    """

    background_tasks.add_task(
        send_email,
        email,
        "Code de vérification du Tournoi",
        html
    )
    return {
        "success": True
    }

# Vérification du code

@router.post("/verify-code")

async def verify_code_api(data: dict):

    # print("ENVCODE =", ENVCODE)
    # bypass en développement
    if ENVCODE == "dev":
        return {
            "success": True
        }
    email = data["email"].strip().lower()
    code = data["code"]
    valid = verify_code(
        email,
        code
    )
    return {
        "success": valid
    }

# Vérification mot de passe
# liste des inscrits

@router.post("/check-liste-password")

async def check_liste_password(data: dict):

    pwd = data.get("pwd")
    if pwd == INSCRIT_PASS:
        return {
            "success": True
        }
    return {
        "success": False
    }