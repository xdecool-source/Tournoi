"""
Gère les : inscriptions, disponibilité des tableaux, classements,
création des paiements HelloAsso, historique des modifications.

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
from services.helloassoClient  import create_checkout

from core.config import (
    TABLEAUX,
    MOCK_FFTT,
)

from api.admin import get_current_admin

from api.cache import (
    places_cache,
    places_cache_time,
    CACHE_TTL
)

import xml.etree.ElementTree as ET
import hashlib
import json
import os
import time

router = APIRouter()

# Variables

HELLOASSO_CARTE = (
    os.getenv("HELLOASSO_CARTE", "true").lower() == "true"
)

INSCRIT_PASS = os.getenv("INSCRIT_PASS")


# ============================================================
# Cache Places
# ============================================================

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
            time.time() - places_cache_time < CACHE_TTL
        )
    ):
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


# ============================================================
# Liste des inscriptions
# ============================================================

@router.get("/inscriptions")
async def inscriptions(
    admin=Depends(get_current_admin)
):
    return await get_all()


# ============================================================
# Classement
# ============================================================

@router.get("/classement")
async def classement(
    admin=Depends(get_current_admin)
):
    return await get_classement_par_tableau()


# ============================================================
# MODIFICATION D'UNE INSCRIPTION
# ============================================================

@router.put("/inscription/{licence}")
async def update_inscription(
    licence: str,
    data: dict,
    background_tasks: BackgroundTasks,
    admin=Depends(get_current_admin)
):

    global places_cache

    # --------------------------------------------------------
    # Sécurité : suppression complète réservée à l'admin
    # --------------------------------------------------------

    if (
        not data.get("tableaux")
        and not admin
    ):
        return {
            "success": False,
            "error": "Suppression réservée admin"
        }

    # --------------------------------------------------------
    # Transaction
    # --------------------------------------------------------

    async with get_conn() as conn:

        async with conn.transaction():

            # =================================================
            # 1. Récupérer les anciens tableaux
            # =================================================

            old_rows = await conn.fetch(
                """
                SELECT tableau
                FROM inscription_tableaux
                WHERE licence=$1
                """,
                licence,
            )

            old_tableaux = {
                r["tableau"]
                for r in old_rows
            }

            # =================================================
            # 1.1 Récupérer le dossard actuel
            # =================================================

            inscription = await conn.fetchrow(
                """
                SELECT dossard, nom, prenom
                FROM inscriptions
                WHERE licence=$1
                """,
                licence,
            )

            if not inscription:
                return {
                    "success": False,
                    "error": "Inscription introuvable"
                }

            dossard = inscription["dossard"]
            
            print(
                "MODIFICATION :",
                "licence =", licence,
                "dossard =", dossard,
                "nom =", inscription["nom"],
                "prenom =", inscription["prenom"]
            )
        
            # =================================================
            # 2. Nouveaux tableaux
            # =================================================

            new_tableaux = set(
                data.get("tableaux", [])
            )
            
            # =================================================
            # 2.1 . Montant avant et après modification
            # =================================================

            
            montant_avant = sum(
                TABLEAUX.get(t, {}).get("prix", 0)
                for t in old_tableaux
            )

            montant_apres = sum(
                TABLEAUX.get(t, {}).get("prix", 0)
                for t in new_tableaux
            )

            difference_montant = (
                montant_apres - montant_avant
            )

            # =================================================
            # 3. Calcul des modifications
            # =================================================

            tableaux_ajoutes = (
                new_tableaux - old_tableaux
            )

            tableaux_supprimes = (
                old_tableaux - new_tableaux
            )

            # =================================================
            # 4. ENREGISTREMENT HISTORIQUE
            #
            # Une seule ligne par modification
            # =================================================

            if (
                tableaux_ajoutes
                or tableaux_supprimes
            ):


                await conn.execute(
                    """
                    INSERT INTO modifications_inscriptions (
                        dossard,
                        licence,
                        nom,
                        prenom,
                        tableaux_avant,
                        tableaux_apres,
                        tableaux_ajoutes,
                        tableaux_supprimes,
                        montant_avant,
                        montant_apres,
                        difference_montant
                        )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5::jsonb,
                        $6::jsonb,
                        $7::jsonb,
                        $8::jsonb,
                        $9,
                        $10,
                        $11
                    )
                    """,
                    dossard,
                    licence,
                    data.get("nom", ""),
                    data.get("prenom", ""),
                    json.dumps(sorted(old_tableaux)),
                    json.dumps(sorted(new_tableaux)),
                    json.dumps(sorted(tableaux_ajoutes)),
                    json.dumps(sorted(tableaux_supprimes)),
                    montant_avant,
                    montant_apres,
                    difference_montant,
                )

            # =================================================
            # 5. SUPPRESSION COMPLÈTE
            # =================================================

            if len(
                data.get(
                    "tableaux",
                    []
                )
            ) == 0:

                # Supprimer les tableaux
                await conn.execute(
                    """
                    DELETE FROM inscription_tableaux
                    WHERE licence=$1
                    """,
                    licence,
                )

                # Supprimer l'inscription
                await conn.execute(
                    """
                    DELETE FROM inscriptions
                    WHERE licence=$1
                    """,
                    licence,
                )

                # Promouvoir les joueurs en attente
                for t in old_tableaux:

                    await promote_attente(t)

                places_cache = None

                # Email
                background_tasks.add_task(
                    send_confirmation_email,
                    data["mail"],
                    data,
                    "suppression",
                )

                return {
                    "success": True
                }

            # =================================================
            # 6. Mise à jour de l'email
            # =================================================

            await conn.execute(
                """
                UPDATE inscriptions
                SET mail=$1
                WHERE licence=$2
                """,
                data["mail"],
                licence,
            )

            # =================================================
            # 7. Suppression anciens tableaux
            # =================================================

            await conn.execute(
                """
                DELETE FROM inscription_tableaux
                WHERE licence=$1
                """,
                licence,
            )

            # =================================================
            # 8. Réinsertion des nouveaux tableaux
            # =================================================

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
                    VALUES ($1,$2,$3)
                    ON CONFLICT
                    (licence,tableau,event_id)
                    DO NOTHING
                    """,
                    licence,
                    t,
                    status,
                )

        # =====================================================
        # 9. Email de confirmation
        # =====================================================

        background_tasks.add_task(
            send_confirmation_email,
            data["mail"],
            data,
            "modification",
        )

        # =====================================================
        # 10. Promouvoir les joueurs quittant un tableau
        # =====================================================

        tableaux_quittes = (
            old_tableaux - new_tableaux
        )

        for t in tableaux_quittes:

            await promote_attente(t)

        # =====================================================
        # 11. Vider le cache
        # =====================================================

        places_cache = None

        return {
            "success": True
        }


# ============================================================
# CRÉATION D'UNE INSCRIPTION
# ============================================================

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

    # --------------------------------------------------------
    # Validation licence
    # --------------------------------------------------------

    if (
        not licence.isdigit()
        or not (3 <= len(licence) <= 8)
    ):
        return {
            "success": False,
            "error": "Licence invalide"
        }

    # --------------------------------------------------------
    # Vérification FFTT
    # --------------------------------------------------------

    if not MOCK_FFTT:

        try:

            xml_data = await appel_fftt(
                "xml_joueur.php",
                {
                    "licence": licence
                }
            )

            root = ET.fromstring(xml_data)

            joueur = root.find(
                ".//joueur"
            )

        except Exception:

            return {
                "success": False,
                "error": (
                    "Service FFTT indisponible. "
                    "Réessayez."
                )
            }

        if joueur is None:

            return {
                "success": False,
                "error": (
                    "Licence introuvable à la FFTT."
                )
            }

    # --------------------------------------------------------
    # Création inscription
    # --------------------------------------------------------

    try:

        # =====================================================
        # Sans HelloAsso
        # =====================================================

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

        # =====================================================
        # Paiement HelloAsso
        # =====================================================

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
        
        