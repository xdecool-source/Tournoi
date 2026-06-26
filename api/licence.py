"""
Vérifie une licence FFTT
Récupère les informations du joueur et contrôle les inscriptions existantes.
GET /licence/{licence}

"""

from fastapi import APIRouter, HTTPException
from core.config import MOCK_FFTT
from services.fftt_service import appel_fftt
from services.db import (
    licence_exists,
    get_tableaux_by_licence,
    get_conn
)

import xml.etree.ElementTree as ET

router = APIRouter()

# Vérification licence FFTT

@router.get("/licence/{licence}")

async def get_licence(licence: str):

    licence = licence.strip()
    # Mode administrateur
    if licence == "999999":
        return {
            "licence": "999999",
            "nom": "MODE",
            "prenom": "ADMIN",
            "mail": "",
            "fftt": True,
            "admin": True
        }
    # Validation du format
    licence = licence.strip()

    if not licence.isdigit() or not (3 <= len(licence) <= 8):
        raise HTTPException(
            status_code=400,
            detail="Licence invalide (3 à 8 chiffres)"
        )

    # Recherche d'une inscription existante
    already = await licence_exists(licence)

    tableaux_inscrits = []
    mail = ""
    if already:
        tableaux_inscrits = await get_tableaux_by_licence(
            licence
        )
        async with get_conn() as conn:
            mail = await conn.fetchval(
                """
                SELECT mail
                FROM inscriptions
                WHERE licence=$1
                """,
                licence
            ) or ""

    # Mode développement

    if MOCK_FFTT:
        return {
            "licence": licence,
            "nom": "Dupond",
            "prenom": "Samuel",
            "club": "Tennis de Table Thuirinois",
            "points": 1000,
            "classement": "NC",
            "categorie": "S",
            "already_inscrit": already,
            "tableaux_inscrits": tableaux_inscrits,
            "mail": mail,
            "fftt": True
        }

    # Appel FFTT

    try:
        xml_data = await appel_fftt(
            "xml_joueur.php",
            {
                "licence": licence
            }
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Service FFTT indisponible. Réessayez dans quelques instants."
        )
    if not xml_data or not xml_data.strip():
        raise HTTPException(
            status_code=503,
            detail="Réponse FFTT vide."
        )

    # Parsing XML

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        raise HTTPException(
            status_code=503,
            detail="Réponse FFTT invalide."
        )
    joueur = root.find(".//joueur")
    if joueur is None:
        raise HTTPException(
            status_code=404,
            detail="Licence introuvable à la FFTT."
        )
    try:

        points = int(
            float(
                joueur.findtext(
                    "valcla",
                    "0"
                )
            )
        )
    except (ValueError, TypeError):
        points = 0
    return {
        "licence": joueur.findtext("licence",licence),
        "nom": joueur.findtext("nom",""),
        "prenom": joueur.findtext("prenom",""),
        "club": joueur.findtext("club",""),
        "points": points,
        "classement": joueur.findtext("valcla",""),
        "categorie": joueur.findtext("categ",""),
        "already_inscrit": already,
        "tableaux_inscrits": tableaux_inscrits,
        "mail": mail,
        "fftt": True
    }