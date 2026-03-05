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

from datetime import datetime
from core.config import BASE_URL, APP_ID, MOT_DE_PASSE, MOCK_FFTT

def generer_serie():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(15))
SERIE_UTILISATEUR = generer_serie()

def timestamp():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + f"{int(now.microsecond/1000):03d}"

def tmc(tm):
    cle = hashlib.md5(MOT_DE_PASSE.encode()).hexdigest()
    return hmac.new(cle.encode(), tm.encode(), hashlib.sha1).hexdigest()

async def appel_fftt(endpoint, params_metier):

    # -----------  MOCK DEV
    
    if MOCK_FFTT:
        licence = params_metier.get("licence")
        return f"""
        <root>
            <joueur>
                <licence>{licence}</licence>
                <nom>Decool</nom>
                <prenom>Xavier</prenom>
                <club>TT Thuirinois</club>
                <clglob>15000</clglob>
                <point>1100</point>
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
    return r.text