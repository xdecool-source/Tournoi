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
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Licence FFTT</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg,#4facfe,#00f2fe);
    display:flex;
    align-items:center;
    justify-content:center;
    height:100vh;
    margin:0;
}

.card {
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 10px 30px rgba(0,0,0,0.2);
    width:350px;
    text-align:center;
}

input {
    width:100%;
    padding:12px;
    border-radius:8px;
    border:1px solid #ddd;
    margin-bottom:10px;
}

button {
    width:100%;
    padding:12px;
    border:none;
    border-radius:8px;
    background:#4facfe;
    color:white;
    cursor:pointer;
}

.player-card {
    background:white;
    padding:20px;
    border-radius:12px;
    margin-top:15px;
    box-shadow:0 5px 20px rgba(0,0,0,0.15);
    text-align:left;
}

.player-name {
    font-size:20px;
    font-weight:bold;
    margin-bottom:8px;
}

.badge {
    background:linear-gradient(45deg,#ff7e5f,#feb47b);
    color:white;
    padding:6px 10px;
    border-radius:6px;
    display:inline-block;
    margin-bottom:10px;
    font-weight:bold;
}

.info {
    line-height:1.6;
    font-size:14px;
}
</style>
</head>

<body>
<div class="card">
<h2>Licence FFTT</h2>
<input id="licence" placeholder="Numéro licence">
<button onclick="check()">Rechercher</button>
<div id="result"></div>
</div>

<script>
async function check(){
    const lic = document.getElementById("licence").value;
    const r = await fetch("/licence/" + lic);
    const data = await r.json();

    document.getElementById("result").innerHTML = `
    <div class="player-card">
        <div class="player-name">${data.prenom} ${data.nom}</div>

        <div class="badge">Classement ${data.classement}</div>

        <div class="info">
            <b>Licence :</b> ${data.licence}<br>
            <b>Club :</b> ${data.club}<br>
            <b>Points :</b> ${Number(data.points).toFixed(1)}<br>
            <b>Catégorie :</b> ${data.categorie}
        </div>
    </div>
    `;
}
</script>

</body>
</html>
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







