"""
Gère les  : inscriptions, disponibilité des tableaux, classements, création des paiements HelloAsso.
cache des places
GET /inscriptions
GET /classement
GET /places
POST /inscription
PUT /inscription/{licence}

"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)

from services.db import (
    save_inscription,
    get_all,
    get_conn,
    count_tableau,
    tableau_status,
    get_classement_par_tableau,
    promote_attente,
)

from services.fftt_service import appel_fftt
from services.mail_inscription import send_confirmation_email
from services.helloasso import create_checkout

from core.config import (
    TABLEAUX,
    MOCK_FFTT,
)

from api.admin import get_current_admin

from api.cache import (
    places_cache,
    places_cache_time,
    CACHE_TTL,
    invalidate_places_cache,
)

import xml.etree.ElementTree as ET
import hashlib
import json
import os
import time

router = APIRouter()

# Variables

HELLOASSO_CARTE = (os.getenv("HELLOASSO_CARTE", "true").lower() == "true")
INSCRIT_PASS = os.getenv("INSCRIT_PASS")

# Cache Places

#places_cache = None
#places_cache_time = 0
#CACHE_TTL = 3

# Liste des inscriptions

@router.get("/inscriptions")

async def inscriptions(
    admin=Depends(get_current_admin)
):
    return await get_all()

# Classement

@router.get("/classement")

async def classement(
    admin=Depends(get_current_admin)
):
    return await get_classement_par_tableau()

# Places restantes

@router.get("/places")

async def get_places(
    request: Request,
    response: Response
):
    global places_cache
    global places_cache_time
    if (
        places_cache
        and (
            time.time()
            - places_cache_time
            < CACHE_TTL
        )
    ):
        res = places_cache
    else:
        res = {}
        for t, conf in TABLEAUX.items():
            ok = await count_tableau(t,"OK")
            attente = await count_tableau(t,"ATTENTE")
            res[t] = {
                "ok": ok,
                "attente": attente,
                "capacite": conf["capacite"],
                "attente_max": conf.get(
                    "attente",
                    0
                ),
            }

        places_cache = res
        places_cache_time = time.time()
        
    etag = hashlib.md5(
        json.dumps(
            res,
            sort_keys=True
        ).encode()
    ).hexdigest()
    
    if (
        request.headers.get("if-none-match")
        == etag
    ):
        response.status_code = 304
        return
    
    response.headers["ETag"] = etag
    return res


async def appliquer_modification(
    licence: str,
    data: dict,
    old_tableaux: set,
    new_tableaux: set,
):
    async with get_conn() as conn:

        async with conn.transaction():

            # Email
            await conn.execute(
                """
                UPDATE inscriptions
                SET mail=$1
                WHERE licence=$2
                """,
                data["mail"],
                licence,
            )

            # Suppression anciens tableaux
            await conn.execute(
                """
                DELETE FROM inscription_tableaux
                WHERE licence=$1
                """,
                licence,
            )

            # Ajout nouveaux tableaux
            for tableau in new_tableaux:

                status = await tableau_status(
                    tableau
                )

                if status == "FULL":
                    status = "ATTENTE"

                await conn.execute(
                    """
                    INSERT INTO inscription_tableaux
                    (
                        licence,
                        tableau,
                        statut
                    )
                    VALUES ($1, $2, $3)
                    ON CONFLICT
                    (
                        licence,
                        tableau,
                        event_id
                    )
                    DO NOTHING
                    """,
                    licence,
                    tableau,
                    status,
                )

            # Tableaux supprimés
            tableaux_quittes = (
                old_tableaux
                - new_tableaux
            )

            for tableau in tableaux_quittes:

                await promote_attente(
                    tableau
                )
                
                



# Modification d'une inscription

@router.put("/inscription/{licence}")
async def update_inscription(
    licence: str,
    data: dict,
    background_tasks: BackgroundTasks,
    admin=Depends(get_current_admin),
):
    # -----------------------------------------
    # Tableaux demandés
    # -----------------------------------------

    new_tableaux = set(
        data.get(
            "tableaux",
            [],
        )
    )

    # -----------------------------------------
    # Suppression complète
    # -----------------------------------------

    if not new_tableaux:

        if not admin:

            return {
                "success": False,
                "error":
                    "Suppression réservée admin",
            }

    # -----------------------------------------
    # Anciens tableaux
    # -----------------------------------------

    async with get_conn() as conn:

        rows = await conn.fetch(
            """
            SELECT tableau
            FROM inscription_tableaux
            WHERE licence=$1
            """,
            licence,
        )

    old_tableaux = {
        row["tableau"]
        for row in rows
    }

    # -----------------------------------------
    # Calcul ancien montant
    # -----------------------------------------

    ancien_total = sum(
        TABLEAUX
        .get(tableau, {})
        .get("prix", 0)
        for tableau in old_tableaux
    )

    # -----------------------------------------
    # Calcul nouveau montant
    # -----------------------------------------

    nouveau_total = sum(
        TABLEAUX
        .get(tableau, {})
        .get("prix", 0)
        for tableau in new_tableaux
    )

    difference = round(
        nouveau_total - ancien_total,
        2,
    )

    # -----------------------------------------
    # Aucun changement
    # -----------------------------------------

    if old_tableaux == new_tableaux:

        return {
            "success": True,
            "payment_required": False,
            "montant": 0,
        }

    # =========================================
    # PAIEMENT SUPPLÉMENTAIRE
    # =========================================

    if (
        difference > 0
        and HELLOASSO_CARTE
    ):

        # -------------------------------------
        # Création de la modification en attente
        # -------------------------------------

        async with get_conn() as conn:

            row = await conn.fetchrow(
                """
                INSERT INTO modification_paiement
                (
                    licence,
                    mail,
                    anciens_tableaux,
                    nouveaux_tableaux,
                    montant,
                    statut,
                    expires_at
                )
                VALUES
                (
                    $1,
                    $2,
                    $3::jsonb,
                    $4::jsonb,
                    $5,
                    'ATTENTE',
                    NOW() + INTERVAL '20 minutes'
                )
                RETURNING id
                """,
                licence,
                data["mail"],
                json.dumps(
                    list(old_tableaux)
                ),
                json.dumps(
                    list(new_tableaux)
                ),
                difference,
            )

            modification_id = row["id"]

        # -------------------------------------
        # Préparation HelloAsso
        # -------------------------------------

        checkout_data = {
            **data,

            "licence":
                licence,

            "tableaux":
                list(new_tableaux),

            "type":
                "modification",

            "modification_id":
                modification_id,
        }

        # -------------------------------------
        # Création paiement
        # -------------------------------------

        try:

            checkout = await create_checkout(
                montant=difference,
                data=checkout_data,
            )

        except Exception as e:

            print(
                "Erreur HelloAsso :",
                e,
            )

            async with get_conn() as conn:

                await conn.execute(
                    """
                    DELETE FROM modification_paiement
                    WHERE id=$1
                    """,
                    modification_id,
                )

            return {
                "success": False,
                "error":
                    "Erreur HelloAsso",
            }

        # -------------------------------------
        # Vérification réponse
        # -------------------------------------

        if "redirectUrl" not in checkout:

            print(
                "HelloAsso KO =",
                checkout,
            )

            async with get_conn() as conn:

                await conn.execute(
                    """
                    DELETE FROM modification_paiement
                    WHERE id=$1
                    """,
                    modification_id,
                )

            return {
                "success": False,
                "error":
                    "Erreur HelloAsso",
            }

        # -------------------------------------
        # ID du paiement
        # -------------------------------------

        paiement_id = (
            checkout.get("id")
            or checkout.get(
                "checkoutIntentId"
            )
        )

        if paiement_id:

            async with get_conn() as conn:

                await conn.execute(
                    """
                    UPDATE modification_paiement
                    SET paiement_id=$1
                    WHERE id=$2
                    """,
                    str(paiement_id),
                    modification_id,
                )

        # -------------------------------------
        # On NE modifie PAS encore la BDD
        # -------------------------------------

        return {
            "success": True,
            "payment_required": True,
            "montant": difference,
            "payment_url":
                checkout["redirectUrl"],
            "modification_id":
                modification_id,
        }

    # =========================================
    # PAS DE PAIEMENT
    # =========================================

    await appliquer_modification(
        licence=licence,
        data=data,
        old_tableaux=old_tableaux,
        new_tableaux=new_tableaux,
    )

    invalidate_places_cache()

    # -----------------------------------------
    # Email
    # -----------------------------------------

    background_tasks.add_task(
        send_confirmation_email,
        data["mail"],
        data,
        "modification",
    )

    return {
        "success": True,
        "payment_required": False,
        "montant": difference,
    }
    
    

# Création d'une inscription

@router.post("/inscription")

async def inscription(
    data: dict,
    background_tasks: BackgroundTasks
):
    licence = str(
        data.get(
            "licence",
            ""
        )
    )

    # Validation licence

    if (
        not licence.isdigit()
        or not (3 <= len(licence) <= 8)
    ):
        return {
            "success": False,
            "error": "Licence invalide"
        }

    # Vérification FFTT

    if not MOCK_FFTT:
        try:
            xml_data = await appel_fftt(
                "xml_joueur.php",
                {
                    "licence": licence
                }
            )
            root = ET.fromstring(xml_data)
            joueur = root.find(".//joueur")
        except Exception:
            return {
                "success": False,
                "error": "Service FFTT indisponible. Réessayez."
            }
        if joueur is None:
            return {
                "success": False,
                "error": "Licence introuvable à la FFTT."
            }

    # Création inscription

    try:
        # Sans HelloAsso

        if not HELLOASSO_CARTE:
            await save_inscription(data)
            background_tasks.add_task(
                send_confirmation_email,
                data["mail"],
                data,
                "creation"
            )
            global places_cache
            places_cache = None
            return {
                "success": True
            }

        # Paiement HelloAsso

        total = sum(
            TABLEAUX.get(
                t,
                {}
            ).get(
                "prix",
                0
            )
            for t in data.get(
                "tableaux",
                []
            )
        )
        data["type"] = "inscription"
        checkout = await create_checkout(
            montant=total,
            data=data
        )
        if "redirectUrl" not in checkout:
            print(
                "HelloAsso KO =",
                checkout
            )
            return {
                "success": False,
                "error": "Erreur HelloAsso"
            }
        return {
            "success": True,
            "montant": total,
            "payment_url": checkout[
                "redirectUrl"
            ]
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        } 
        
        
async def appliquer_modification(
    licence: str,
    data: dict,
    old_tableaux: set,
    new_tableaux: set,
):
    async with get_conn() as conn:
        async with conn.transaction():

            # Mise à jour de l'email
            await conn.execute(
                """
                UPDATE inscriptions
                SET mail=$1
                WHERE licence=$2
                """,
                data["mail"],
                licence,
            )

            # Suppression des anciens tableaux
            await conn.execute(
                """
                DELETE FROM inscription_tableaux
                WHERE licence=$1
                """,
                licence,
            )

            # Ajout des nouveaux tableaux
            for t in new_tableaux:

                status = await tableau_status(t)

                if status == "FULL":
                    status = "ATTENTE"

                await conn.execute(
                    """
                    INSERT INTO inscription_tableaux
                    (
                        licence,
                        tableau,
                        statut
                    )
                    VALUES ($1, $2, $3)
                    ON CONFLICT
                    (
                        licence,
                        tableau,
                        event_id
                    )
                    DO NOTHING
                    """,
                    licence,
                    t,
                    status,
                )

            # Les tableaux abandonnés libèrent une place
            tableaux_quittes = (
                old_tableaux - new_tableaux
            )

            for t in tableaux_quittes:
                await promote_attente(t)
