import xml.etree.ElementTree as ET
import urllib.parse
import httpx
import hashlib
import hmac
import random
import string
import os

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

# ===============================
# CONFIG RENDER
# ===============================
BASE_URL = os.getenv("BASE_URL")
APP_ID = os.getenv("APP_ID")
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE")

if not BASE_URL or not APP_ID or not MOT_DE_PASSE:
    raise Exception("Variables d'environnement FFTT manquantes")

app = FastAPI()

# ===============================
# SERIE UTILISATEUR
# ===============================
def generer_serie():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(15))

SERIE_UTILISATEUR = generer_serie()

# ===============================
# TIMESTAMP + CRYPTO FFTT
# ===============================
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

# ===============================
# PAGE INTERACTIVE
# ===============================
@app.get("/", response_class=HTMLResponse)
def home():
    html = """
    <h2>Recherche licence FFTT</h2>
    <input id="licence" placeholder="Licence FFTT">
    <button onclick="check()">Rechercher</button>
    <pre id="result"></pre>

    <script>
    async function check(){
        const lic = document.getElementById("licence").value;
        const r = await fetch("/licence/" + lic);
        const data = await r.json();
        document.getElementById("result").innerText =
            JSON.stringify(data,null,2);
    }
    </script>
    """
    return html

# ===============================
# ENDPOINT LICENCE FFTT
# ===============================
@app.get("/licence/{licence}")
async def get_licence(licence: str):
    try:
        xml_data = await appel_fftt("xml_joueur.php", {"licence": licence})

        root = ET.fromstring(xml_data)
        joueur = root.find(".//joueur")

        if joueur is None:
            raise Exception("Licence introuvable")

        return {
            "licence": joueur.findtext("licence", ""),
            "nom": joueur.findtext("nom", ""),
            "prenom": joueur.findtext("prenom", ""),
            "club": joueur.findtext("club", ""),
            "classement": joueur.findtext("clglob", ""),
            "points": joueur.findtext("point", ""),
            "categorie": joueur.findtext("categ", "")
        }

    except Exception as e:
        raise HTTPException(400, str(e))
