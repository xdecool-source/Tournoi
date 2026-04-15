# gère les routes API du site
# vérifie les licences FFTT
# enregistre les inscriptions aux tableaux
# envoie les emails de confirmation
# gère les places restantes
# fournit les exports admin
# gère login admin

from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks, Header, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from core.config import TABLEAUX, PRIX, ADMIN_PASSWORD_HASH, MOCK_FFTT
from services.fftt_service import appel_fftt
from services.mail_inscription import send_email, send_confirmation_email
from services.mail_code import store_verification_code, verify_code
from dotenv import load_dotenv
from userinterface.screens import home_screen
from export.generate_inscription import generate 
from services.admin_ex_mail import process_admin_export
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError


import xml.etree.ElementTree as ET
import time
import hashlib
import json
import bcrypt
import os

from services.db import (
    save_inscription,
    licence_exists,
    get_all,
    get_conn,
    count_tableau,
    get_tableaux_by_licence,
    tableau_status,
    get_classement_par_tableau,
    promote_attente
)

#  cache places 

places_cache = None
places_cache_time = 0
CACHE_TTL = 3

#  Backend 

router = APIRouter()

#  Début token

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquante")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10  # 10 mn

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True} 
        )
        # print("PAYLOAD:", payload)
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        return payload
    except ExpiredSignatureError:
        # print("TOKEN EXPIRE")
        raise HTTPException(401, "Token expiré")
    except JWTError as e:
        # print("JWT ERROR:", e)
        raise HTTPException(401, "Token invalide")

def get_current_admin(request: Request):
    token = request.cookies.get("access_token")
    
    # print("TOKEN:", token) 
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    payload = verify_token(token) 
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return home_screen(request)

@router.get("/tableaux")
async def get_tableaux():
    result = {}

    for key, conf in TABLEAUX.items():
        result[key] = {
            **conf,
            "prix": PRIX.get(key, 0)
        }
    return result

#  licence fftt 

async def check_fftt_player(licence: str):
    try:
        xml_data = await appel_fftt("xml_joueur.php", {"licence": licence})
        if not xml_data.strip():
            return None
        root = ET.fromstring(xml_data)
        return root.find(".//joueur")
    except Exception:
        return None
    
@router.get("/licence/{licence}")

async def get_licence(licence: str):
    if not licence.isdigit():
        raise HTTPException(400, "Licence numérique obligatoire")
    already = await licence_exists(licence)
    tableaux_inscrits = []
    # mail = "xavier.decool@outlook.com"  
    mail = ""
    
    if already:
        tableaux_inscrits = await get_tableaux_by_licence(licence)
        async with get_conn() as conn:
            mail = await conn.fetchval(
                "SELECT mail FROM inscriptions WHERE licence=$1",
                licence
            ) or ""
    
    xml_data = await appel_fftt("xml_joueur.php", {"licence": licence})
    root = ET.fromstring(xml_data)
    joueur = root.find(".//joueur")
    if joueur is not None:
        points_raw = joueur.findtext("point", "0")
        try:
            points = int(float(points_raw))
        except:
            points = 0
        return {
            "licence": joueur.findtext("licence", licence),
            "nom": joueur.findtext("nom", ""),
            "prenom": joueur.findtext("prenom", ""),
            "club": joueur.findtext("club", ""),
            "points": points,
            "classement": joueur.findtext("clglob", ""),
            "categorie": joueur.findtext("categ", ""),
            "already_inscrit": already,
            "tableaux_inscrits": tableaux_inscrits,
            "mail": mail,
            "fftt": True
        }
        
#  Mode fftt réel

    joueur = await check_fftt_player(licence)

    if joueur is not None:
        points_raw = joueur.findtext("point", "0")
        try:
            points = int(float(points_raw))
        except:
            points = 0
        return {
            "licence": joueur.findtext("licence", licence),
            "nom": joueur.findtext("nom", ""),
            "prenom": joueur.findtext("prenom", ""),
            "club": joueur.findtext("club", ""),
            "points": points,
            "classement": joueur.findtext("clglob", ""),
            "categorie": joueur.findtext("categ", ""),
            "already_inscrit": already,
            "tableaux_inscrits": tableaux_inscrits,
            "mail": mail,
            "fftt": True
        }
#   Inconnu FFTT
    return {
        "licence": licence,
        "nom": "Inconnu FFTT",
        "prenom": "Inconnu FFTT",
        "club": "TT Inconnu",
        "points": "1000",
        "classement": "00",
        "categorie": "Inconnu",
        "already_inscrit": already,
        "tableaux_inscrits": tableaux_inscrits,
        "mail": mail,
        "fftt": False
    }

#  inscriptions 

router.get("/inscriptions")

async def inscription(admin=Depends(get_current_admin)):
    return await get_all()

@router.get("/classement")

async def classement(admin=Depends(get_current_admin)):
    return await get_classement_par_tableau()

@router.get("/places")

async def get_places(request: Request, response: Response):
    
    global places_cache, places_cache_time
    
    #  cache valide ?
    if places_cache and (time.time() - places_cache_time < CACHE_TTL):
        res = places_cache
    else:
        res = {}
        for t, conf in TABLEAUX.items():
            ok = await count_tableau(t, "OK")
            attente = await count_tableau(t, "ATTENTE")

            res[t] = {
                "ok": ok,
                "attente": attente,
                "capacite": conf["capacite"],
                "attente_max": conf.get("attente", 0)
            }
        places_cache = res
        places_cache_time = time.time()
        
    #  ETag (compatible cache navigateur : identifiant d’une version de donnée)
    
    etag = hashlib.md5(json.dumps(res, sort_keys=True).encode()).hexdigest()
    if request.headers.get("if-none-match") == etag:
        response.status_code = 304
        return
    response.headers["ETag"] = etag
    return res

#  update inscription 

from fastapi import Depends

@router.put("/inscription/{licence}")
async def update_inscription(
    licence: str,
    data: dict,
    background_tasks: BackgroundTasks,
    admin=Depends(get_current_admin)   
):
    # print("ROUTE UPDATE APPELEE")  # 
    # raise HTTPException(403, "Admin only")
    
    async with get_conn() as conn:
        async with conn.transaction(): 
            
            # 1 récupérer anciens tableaux
            
            old_rows = await conn.fetch("""
                SELECT tableau FROM inscription_tableaux
                WHERE licence=$1
            """, licence)
            old_tableaux = {r["tableau"] for r in old_rows}
            new_tableaux = set(data["tableaux"])
            
            # 2 update mail
            
            await conn.execute(
                "UPDATE inscriptions SET mail=$1 WHERE licence=$2",
                data["mail"], licence
            )
            
            # 3 supprimer anciens tableaux
            
            await conn.execute(
                "DELETE FROM inscription_tableaux WHERE licence=$1",
                licence
            )
            
            # 4 réinsérer nouveaux tableaux
            
            for t in new_tableaux:
                status = await tableau_status(t)
                if status == "FULL":
                    status = "ATTENTE"
                await conn.execute("""
                    INSERT INTO inscription_tableaux
                    (licence, tableau, statut)
                    VALUES ($1,$2,$3)
                """, licence, t, status)

        total = sum(PRIX.get(t, 0) for t in data["tableaux"])
        email_type = "suppression" if total == 0 else "modification"
        
        background_tasks.add_task(
            send_confirmation_email,
            data["mail"],
            data,
            email_type
        )

    # 5 promotion après suppression
    
    tableaux_quittes = old_tableaux - new_tableaux
    for t in tableaux_quittes:
        await promote_attente(t)
    global places_cache
    places_cache = None
    return {"success": True}

#  inscription ( Gestion erreur fftt ) 

@router.post("/inscription")

async def inscription(data: dict, background_tasks: BackgroundTasks):

    licence = str(data.get("licence", ""))
    if not licence.isdigit():
        return {"success": False, "error": "Licence numérique obligatoire"}
    #  Bloquage fftt
    
    if not MOCK_FFTT:
        joueur = await check_fftt_player(licence)
        if joueur is None:
            return {"success": False, "error": "Licence inconnue FFTT"}
    try:
        await save_inscription(data)
        print("Inscription Ok - lancement mail")
        
        # Send mail joueur
        background_tasks.add_task(
            send_confirmation_email,
            data["mail"],
            data,
            "creation"
        )
        global places_cache
        places_cache = None
        return {"success": True}
    except ValueError as e:
        return {"success": False, "error": str(e)}

#  export excel 

@router.get("/export-excel")
async def export_excel(admin=Depends(get_current_admin)):
    stream = generate()
    if not stream:
        raise HTTPException(404, "Aucune donnée")
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=Inscriptions.xlsx"
        }
    )

#  Admin 

@router.get("/me")
def me(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return {"admin": False}
    try:
        payload = verify_token(token)
        return {"admin": payload.get("role") == "admin"}
    except:
        return {"admin": False}
    
@router.post("/login-admin")

def login_admin(data: dict, response: Response): 
    
    # print("LOGIN -> NEW TOKEN ")
    
    if bcrypt.checkpw(
        data.get("pwd", "").encode(),
        ADMIN_PASSWORD_HASH.encode()
    ):
        token = create_access_token({"role": "admin"})
        IS_PROD = os.getenv("ENV") == "prod"
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=IS_PROD,
            samesite="none" if IS_PROD else "lax",
            path="/"
        )
        
        return {"success": True}
    return {"success": False}

@router.post("/logout-admin")
def logout_admin(response: Response):
    response.delete_cookie("access_token")
    return {"success": True}


#  Verification Mail  

@router.post("/send-code")

async def send_code(data: dict, background_tasks: BackgroundTasks):

    email = data["email"].strip().lower()
    try:
        code = store_verification_code(email)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    html = f"""
    <h2>Voici votre Code de vérification pour votre Mail </h2>
    <p>Votre code est :</p>
    <h1>{code}</h1>
    """
    background_tasks.add_task(
        send_email,
        email,
        "Code de vérification - Homopongistus",
        html
    )
    
    return {"success": True} 

@router.post("/verify-code")

async def verify_code_api(data: dict):

    email = data["email"].strip().lower()
    code = data["code"]
    # print("VERIFY CALL:", email, code)
    valid = verify_code(email, code)
    return {"success": valid}


@router.post("/admin/export")
async def download_excel(admin=Depends(get_current_admin)):
    
    # check_admin(x_api_key)

    excel_stream = generate()
    if not excel_stream:
        raise HTTPException(status_code=500, detail="Erreur génération Excel")
    excel_stream.seek(0)
    
    #  nom dynamique
    
    filename = datetime.now().strftime("Inscriptions_Tournoi_%d-%m-%Y_%Hh%M.xlsx")

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )