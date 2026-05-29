# appeler l’API de la FFTT
# récupérer les informations d’un joueur
# générer les paramètres de sécurité (tm, tmc, série)
# fournir un mode mock (imiter , simuler )pour le développement

import os
import urllib.parse
import httpx
import hashlib
import hmac
import random
import string

from datetime import datetime, timezone
from core.config import BASE_URL, APP_ID, MOT_DE_PASSE, MOCK_FFTT

# ce numéro est calculé une seule fois au démarrage de l'APP

if not BASE_URL:
    raise RuntimeError("BASE_URL manquant")

if not APP_ID:
    raise RuntimeError("APP_ID manquant")

if not MOT_DE_PASSE:
    raise RuntimeError("MOT_DE_PASSE manquant")


# Calculé une seule fois au démarrage
CLE_FFTT = hashlib.md5(MOT_DE_PASSE.encode()).hexdigest()

def generer_serie():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(15))

SERIE_UTILISATEUR = generer_serie()

def timestamp():
    now = datetime.now(timezone.utc)
    # now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + f"{int(now.microsecond/1000):03d}"

def tmc(tm):
    return hmac.new(
        CLE_FFTT.encode(),
        tm.encode(),
        hashlib.sha1
    ).hexdigest()
    
    
async def appel_fftt(endpoint, params_metier):

#   Mock Dev 
#   Simule un retour xml
    
    if MOCK_FFTT:
        licence = params_metier.get("licence", "000000")

        joueurs = {
            "111": ("Dupond", "Xavier", "Perpignan TT", 850),
            "222": ("Durand", "Paul", "Montpellier TT", 1450),
            "333": ("Martin", "Luc", "Toulouse TT", 2000),   
            "444": ("Albert", "loic", "Foix TT", 1250),
            "555": ("Foix", "Samuel", "Cac TT", 620)
        }

        nom, prenom, club, point = joueurs.get(
            licence,
            ("Le Joueur", "Xavier", "Perpignan La Rayonnante", 1000)
        )

        return f"""
        <root>
            <joueur>
                <licence>{licence}</licence>
                <nom>{nom}</nom>
                <prenom>{prenom}</prenom>
                <club>{club}</club>
                <valcla>{point}</valcla>
                <point>{point}</point>
                <categ>S</categ>
            </joueur>
        </root>
        """
    tm = timestamp()
    params = {
        "id": APP_ID,
        "serie": SERIE_UTILISATEUR,
        "tm": tm,
        "tmc": tmc(tm),
        **params_metier
    }

    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
    return r.text