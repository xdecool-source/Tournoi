import os
import random
import string
import hashlib
import hmac
import urllib.parse
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from fastapi import FastAPI, HTTPException

BASE_URL = os.getenv("BASE_URL")
APP_ID = os.getenv("APP_ID")
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE")

app = FastAPI()

print("BASE_URL =", BASE_URL)
print("APP_ID =", APP_ID)
print("MOT_DE_PASSE =", MOT_DE_PASSE)


# =========================
# SERIE (en mémoire Render)
# =========================
def generer_serie():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(15))

SERIE_UTILISATEUR = generer_serie()

# =========================
# OUTILS FFTT
# =========================
def timestamp():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + f"{int(now.microsecond/1000):03d}"

def tmc(tm):
    cle = hashlib.md5(MOT_DE_PASSE.encode()).hexdigest()
    return hmac.new(cle.encode(), tm.encode(), hashlib.sha1).hexdigest()

async def appel_fftt(endpoint, params_metier):
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

# =========================
# ENDPOINT LICENCE
# =========================
@app.get("/licence/{licence_id}")
async def licence(licence_id: str):
    try:
        xml_data = await appel_fftt(
            "xml_licence_b.php",
            {"licence": licence_id}
        )

        root = ET.fromstring(xml_data)

        nom = (
            root.findtext(".//nom", "") + " " +
            root.findtext(".//prenom", "")
        ).strip()

        club = root.findtext(".//nomclub", "")
        points = root.findtext(".//point", "")

        if not nom:
            raise Exception("Licence introuvable")

        return {
            "nom": nom,
            "club": club,
            "points": points
        }

    except Exception as e:

        raise HTTPException(400, str(e))
