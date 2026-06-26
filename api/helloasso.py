"""
Reçoit les webhooks/callbacks de HelloAsso et enregistre les inscriptions payées.
GET /helloasso/callback
POST /helloasso/webhook
GET /paiement-ok",response_class=HTMLResponse

"""

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.db import (
    save_inscription,
    licence_exists,
)

from services.mail_inscription import (
    send_confirmation_email,
)

import api.cache as cache
cache.places_cache = None

router = APIRouter()

templates = Jinja2Templates(
    directory="userinterface/templates"
)

HELLOASSO_CARTE = (
    os.getenv(
        "HELLOASSO_CARTE",
        "true"
    ).lower() == "true"
)

# Callback HelloAsso

if HELLOASSO_CARTE:

    @router.get("/helloasso/callback")
    
    async def helloasso_callback():
        return {
            "status": "ok"
        }

    # Webhook HelloAsso

    @router.post("/helloasso/webhook")
    
    async def helloasso_webhook(
        request: Request
    ):
        payload = await request.json()
        print(
            "Webhook HelloAsso reçu : "
            f"event={payload.get('eventType')}"
        )
        if payload["eventType"] != "Order":

            return {
                "ok": True
            }
        meta = payload["metadata"]
        data = {
            "licence":
                meta["licence"],
            "nom":
                meta["nom"],
            "prenom":
                meta["prenom"],
            "club":
                meta["club"],
            "points":
                int(meta["points"]),
            "mail":
                meta["email"],
            "tableaux":
                meta["tableaux"].split(","),
            "paiement":
                "HelloAsso",
            "helloasso_order_id":
                payload.get(
                    "data",
                    {}
                ).get("id")
        }

        already = await licence_exists(
            meta["licence"]
        )
        if already:
            print(
                "Licence déjà inscrite :",
                meta["licence"]
            )
            return {
                "ok": True
            }
        await save_inscription(
            data
        )
        await send_confirmation_email(
            meta["email"],
            data,
            "creation"

        )

        # invalider le cache des places
        #
        # IMPORTANT :
        # si tu gardes places_cache dans
        # api.inscription il faudra faire :
        #
        # import api.inscription as inscription
        # inscription.places_cache = None
        #
        # ou mieux :
        # déplacer le cache dans un module
        # api/cache.py

        print(
            "Inscription enregistrée"
        )
        return {
            "ok": True
        }

# Page retour paiement

@router.get("/paiement-ok",response_class=HTMLResponse)

async def paiement_ok(
    request: Request
):
    return templates.TemplateResponse(
        "paiement_ok.html",
        {
            "request": request
        }
    )