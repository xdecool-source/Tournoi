# gère les routes API du site
# vérifie les licences FFTT
# enregistre les inscriptions aux tableaux
# envoie les emails de confirmation
# gère les places restantes
# fournit les exports admin
# gère login admin et durée de vie de la session 

from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks, Header, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from core.config import TABLEAUX, ADMIN_PASS_HASH, MOCK_FFTT
from services.fftt_service import appel_fftt

from services.mail_code import send_email
from services.mail_code import store_verification_code, verify_code
from services.mail_inscription import send_confirmation_email

from dotenv import load_dotenv
from export.generate_inscription import generate 
from datetime import datetime, timedelta, date
from jose import jwt, JWTError, ExpiredSignatureError
from os import getenv

from userinterface.screens import templates, MOIS_FR
# from userinterface.screens import home_screen


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

templates = Jinja2Templates(directory="userinterface/templates")

#  cache places 

places_cache = None
places_cache_time = 0
CACHE_TTL = 3

#  Backend 

router = APIRouter()
ENV = os.getenv("ENV", "dev")
ENVCODE = os.getenv("ENVCODE", "dev")
INSCRIT_PASS = os.getenv("INSCRIT_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")
NBRE_TABLEAU = os.getenv("NBRE_TABLEAU")
DATE_TOURNOI = os.getenv("DATE_TOURNOI")
DATE_TOURNOI_JOUR = os.getenv("DATE_TOURNOI_JOUR")
NOM_TOURNOI = os.getenv("NOM_TOURNOI")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    date_obj = datetime.strptime(DATE_TOURNOI, "%d/%m/%Y")
    date_formatee = f"{date_obj.day} {MOIS_FR[date_obj.month]} {date_obj.year}"

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "NBRE_TABLEAU": NBRE_TABLEAU,
            "DATE_TOURNOI": date_formatee,
            "DATE_TOURNOI_JOUR": DATE_TOURNOI_JOUR,
            "NOM_TOURNOI": NOM_TOURNOI,
            "FROM_EMAIL": FROM_EMAIL
        }
    )
    
#  Début token

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquante")

ALGORITHM = "HS256"
TIME_ADMIN_SESSION = int(os.getenv("TIME_ADMIN_SESSION", 15))
ACCESS_TOKEN_EXPIRE_MINUTES = TIME_ADMIN_SESSION

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

@router.get("/tableaux")
async def get_tableaux():
    result = {}

    for key, conf in TABLEAUX.items():
        result[key] = {
            **conf,
            "prix": conf.get("prix", 0)
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

@router.put("/inscription/{licence}")
async def update_inscription(
    licence: str,
    data: dict,
    background_tasks: BackgroundTasks,
    admin=Depends(get_current_admin)   
):
    global places_cache

    # print("ROUTE UPDATE APPELEE")  # 
    # raise HTTPException(403, "Admin only")
    # on block en cas de non saisi de tableau sans etre admin 
    if not data.get("tableaux") and not admin:
        return {"success": False, "error": "Suppression réservée admin"}
    
    async with get_conn() as conn:
        async with conn.transaction(): 
            
            # 1 récupérer anciens tableaux
            
            old_rows = await conn.fetch("""
                SELECT tableau FROM inscription_tableaux
                WHERE licence=$1
            """, licence)
            old_tableaux = {r["tableau"] for r in old_rows}
            new_tableaux = set(data["tableaux"])
            
            if len(data.get("tableaux", [])) == 0:
                
                # supprimer tableaux
                await conn.execute(
                    "DELETE FROM inscription_tableaux WHERE licence=$1",
                    licence
                )

                # supprimer inscription
                await conn.execute(
                    "DELETE FROM inscriptions WHERE licence=$1",
                    licence
                )

                # promotion attente
                for t in old_tableaux:
                    await promote_attente(t)

                global places_cache
                places_cache = None

                background_tasks.add_task(
                    send_confirmation_email,
                    data["mail"],
                    data,
                    "suppression"
                )

                return {"success": True}
            
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
                    ON CONFLICT (licence, tableau, event_id) DO NOTHING
                """, licence, t, status)

        total = sum(TABLEAUX.get(t, {}).get("prix", 0) for t in data["tableaux"])
        # email_type = "suppression" if total == 0 else "modification"
        
        background_tasks.add_task(
            send_confirmation_email,
            data["mail"],
            data,
            "modification"
        )

            # 5 promotion après suppression
            
        tableaux_quittes = old_tableaux - new_tableaux
        for t in tableaux_quittes:
            await promote_attente(t)   
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
        # print("Inscription Ok - lancement mail")
        
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

    now = datetime.now().strftime("%d-%m-%Y_%Hh%M")

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="Inscriptions_Tournoi_{now}.xlsx"'
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
        ADMIN_PASS_HASH.encode()
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
    <h2>Voici votre Code de vérification pour valider votre Mail <h1>{code}</h1> </h2>
    <p>Ce code expire dans 5 minutes.</p>
    <p>De plus avec le Mot de passe liste inscrits ci-joint :
    <b>{INSCRIT_PASS}</b>
    vous avez la possibilite de consulter tous les inscrits.
    il faut saisir votre licence et cliquer sur le bouton liste inscrits en bas à droite
    </p>
    <p>Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer ce message.</p>
    """
    background_tasks.add_task(
        send_email,
        email,
        "Code de vérification du Tournoi",
        html
    )
    
    return {"success": True} 

@router.post("/verify-code")

async def verify_code_api(data: dict):
    # bypass en dev
    # print("ROUTE VERIFY APPELEE")
    if ENVCODE == "dev":
        return {"success": True}
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
    

@router.post("/check-liste-password")
async def check_liste_password(data: dict):

    pwd = data.get("pwd")
    if pwd == INSCRIT_PASS:
        return {"success": True}
    return {"success": False}

@router.get("/inscrits")
async def get_inscrits():

    try:
        async with get_conn() as conn:
            rows = await conn.fetch("""

                -- JOUEURS ACTIFS
                SELECT i.dossard, i.licence, i.nom, i.prenom, i.club, i.points,
                    COALESCE(
                        array_agg(
                            CASE
                                WHEN it.statut = 'ATTENTE'
                                THEN it.tableau || '_ATTENTE'
                                ELSE it.tableau
                            END
                        )
                        FILTER (
                            WHERE it.tableau IS NOT NULL
                        ),
                        '{}'
                    ) AS tableaux,
                    FALSE AS annule
                FROM inscriptions i
                LEFT JOIN inscription_tableaux it
                    ON i.licence = it.licence
                GROUP BY i.dossard, i.licence, i.nom, i.prenom, i.club, i.points
                UNION ALL
                
                -- JOUEURS ANNULES
                SELECT
                    di.dossard, di.licence, di.nom, di.prenom, di.club, di.points,
                    ARRAY[]::text[] AS tableaux,
                    TRUE AS annule
                FROM delete_inscrit di
                ORDER BY annule ASC, points DESC
            """)

            inscrits = []

            for r in rows:

                inscrits.append({

                    "dossard": r["dossard"],
                    "licence": r["licence"],
                    "nom": r["nom"],
                    "prenom": r["prenom"],
                    "club": r["club"],
                    "points": r["points"],
                    "tableaux": r["tableaux"],
                    "annule": r["annule"]

                })
        return {
            "success": True,
            "inscrits": inscrits
        }

    except Exception as e:

        print("ERREUR EXPORT INSCRITS :", e)
        return {
            "success": False,
            "error": "Erreur serveur"

        }
        
@router.get("/export-inscrits", response_class=HTMLResponse)
async def export_inscrits_page(request: Request):

    return templates.TemplateResponse(
        "exportInscrits.html",
        {
            "request": request,
            "INSCRIT_PASS": INSCRIT_PASS
        }
    )