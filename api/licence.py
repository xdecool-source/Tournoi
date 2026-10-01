"""
Vérifie une licence FFTT
Récupère les informations du joueur et contrôle les inscriptions existantes.
GET /licence/{licence}
"""

from fastapi import APIRouter, HTTPException

from core.config import FFTT_API
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
   
    # Validation du format

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
        tableaux_inscrits = await get_tableaux_by_licence(licence)
        async with get_conn() as conn:
            mail = await conn.fetchval(
                """
                SELECT mail
                FROM inscriptions
                WHERE licence=$1
                """,
                licence
            ) or ""
    # Appel FFTT
    # Le service appel_fftt() gère lui-même :
    # - le mode FFTT_API
    # - l'API FFTT réelle

    try:
        xml_data = await appel_fftt("xml_joueur.php",{"licence": licence})
    except Exception as e:
        print("ERREUR FFTT :", e)
        raise HTTPException(status_code=503,detail=("Service FFTT indisponible. ""Réessayez dans quelques instants."))
    # Vérification réponse

    if not xml_data or not xml_data.strip():
        raise HTTPException(status_code=503,detail="Réponse FFTT vide.")
    # Parsing XML
    
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print("ERREUR XML :", e)
        raise HTTPException(status_code=503,detail="Réponse FFTT invalide.")
    # Recherche du joueur

    joueur = root.find(".//joueur")
    if joueur is None:
        raise HTTPException(status_code=404,detail="Licence introuvable à la FFTT.")
    # Récupération des points
    
    try:
        points = int(float(joueur.findtext("valcla","0")))
    except (ValueError, TypeError):
        points = 0
    # Récupération des informations

    licence_xml = joueur.findtext("licence",licence)
    nom = joueur.findtext("nom","")
    prenom = joueur.findtext("prenom","")
    club = joueur.findtext("club","")
    classement = joueur.findtext("valcla","")
    categorie = joueur.findtext("categ","")
    # Réponse API

    return {
        "licence": licence_xml,"nom": nom,"prenom": prenom,"club": club,"points": points,"classement": classement,
        "categorie": categorie,"already_inscrit": already,"tableaux_inscrits": tableaux_inscrits,
        "mail": mail,"fftt": True
    }
    