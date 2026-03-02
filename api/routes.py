from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
import xml.etree.ElementTree as ET

from services.fftt_service import appel_fftt
from ui.screens import home_screen
from core.config import TABLEAUX, ADMIN_PASSWORD_HASH, MOCK_FFTT
from fastapi import BackgroundTasks
from services.mail_service import send_confirmation_email

import time
import hashlib
import json
import bcrypt


from services.db import (
    save_inscription,
    licence_exists,
    get_all,
    get_conn,
    count_tableau,
    get_tableaux_by_licence,
    tableau_status,
    get_classement_par_tableau,
    check_and_trigger_export,
    promote_attente
)
#  CACHE PLACES (ICI)
places_cache = None
places_cache_time = 0
CACHE_TTL = 5

# Backend 
router = APIRouter()

# ---------- HOME ----------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return home_screen(request)

@router.get("/tableaux")
async def get_tableaux():
    return TABLEAUX

# ---------- LICENCE FFTT ----------
async def check_fftt_player(licence: str):
    """Retourne joueur FFTT ou None"""
    if MOCK_FFTT:
        return None   #  IMPORTANT
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
    mail = f"{licence}@mock.fr"   #  FIX

    if already:
        tableaux_inscrits = await get_tableaux_by_licence(licence)
        async with get_conn() as conn:
            mail = await conn.fetchval(
                "SELECT mail FROM inscriptions WHERE licence=$1",
                licence
            ) or ""

    #  MODE MOCK → joueur fictif mais VALIDE
    if MOCK_FFTT:
        return {
            "licence": licence,
            "nom": "No Access FFTT",
            "prenom": "Player",
            "club": "Club Mock",
            "points": "1000",
            "classement": "10",
            "categorie": "Senior",
            "already_inscrit": already,
            "tableaux_inscrits": tableaux_inscrits,
            "mail": mail,
            "fftt": True
        }

    #  MODE FFTT RÉEL
    joueur = await check_fftt_player(licence)

    if joueur is not None:
        return {
            "licence": joueur.findtext("licence", licence),
            "nom": joueur.findtext("nom", ""),
            "prenom": joueur.findtext("prenom", ""),
            "club": joueur.findtext("club", ""),
            "points": joueur.findtext("point", ""),
            "classement": joueur.findtext("clglob", ""),
            "categorie": joueur.findtext("categ", ""),
            "already_inscrit": already,
            "tableaux_inscrits": tableaux_inscrits,
            "mail": mail,
            "fftt": True
        }

    #  inconnu FFTT
    return {
        "licence": licence,
        "nom": "Inconnu",
        "prenom": "Inconnu",
        "club": "TT Inconnu",
        "points": "1000",
        "classement": "00",
        "categorie": "Inconnu",
        "already_inscrit": already,
        "tableaux_inscrits": tableaux_inscrits,
        "mail": mail,
        "fftt": False
    }



# ---------- INSCRIPTIONS ----------
@router.get("/inscriptions")
async def inscriptions():
    return await get_all()

@router.get("/classement")
async def classement():
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

    #  ETag (compatible cache navigateur)
    etag = hashlib.md5(json.dumps(res, sort_keys=True).encode()).hexdigest()

    if request.headers.get("if-none-match") == etag:
        response.status_code = 304
        return

    response.headers["ETag"] = etag
    return res

# ---------- UPDATE INSCRIPTION ----------
@router.put("/inscription/{licence}")
async def update_inscription(licence: str, data: dict, request: Request, background_tasks: BackgroundTasks):

    if request.cookies.get("admin") != "1":
        raise HTTPException(403, "Admin only")

    async with get_conn() as conn:
        async with conn.transaction():  #  sécurise tout

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

        await check_and_trigger_export(conn)
        
        background_tasks.add_task(
            send_confirmation_email,
            data["mail"],
            data,
            "modification"
        )

        #  FIN TRANSACTION

    # 5 promotion après suppression
    tableaux_quittes = old_tableaux - new_tableaux

    for t in tableaux_quittes:
        await promote_attente(t)

    global places_cache
    places_cache = None

    return {"success": True}



# ---------- INSCRIPTION ( BLOQUAGE FFTT) ----------
@router.post("/inscription")
async def inscription(data: dict, background_tasks: BackgroundTasks):

    licence = str(data.get("licence", ""))

    if not licence.isdigit():
        return {"success": False, "error": "Licence numérique obligatoire"}

    #  BLOQUAGE FFTT
    if not MOCK_FFTT:
        joueur = await check_fftt_player(licence)
        if joueur is None:
            return {"success": False, "error": "Licence inconnue FFTT"}

    try:
        await save_inscription(data)
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
    
    
# ---------- ADMIN ----------
@router.post("/login-admin")
def login_admin(data: dict, response: Response):
    if bcrypt.checkpw(
        data.get("pwd", "").encode(),
        ADMIN_PASSWORD_HASH.encode()
        ):
        response.set_cookie("admin", "1")
        return {"success": True}
    return {"success": False}


@router.post("/logout-admin")
def logout_admin(response: Response):
    response.delete_cookie("admin")
    return {"success": True}
