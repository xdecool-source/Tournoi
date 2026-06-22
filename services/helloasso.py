import os
import httpx

CLIENT_ID = os.getenv("HELLOASSO_CLIENT_ID")
CLIENT_SECRET = os.getenv("HELLOASSO_CLIENT_SECRET")


async def get_token():

    async with httpx.AsyncClient() as client:

        response = await client.post(
            "https://api.helloasso.com/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
        )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]

import httpx
import os

ORGANIZATION = "tennis-de-table-thuirinois"

async def create_checkout(montant, data):

    token = await get_token()

    payload = {
        "totalAmount": int(montant * 100),
        "initialAmount": int(montant * 100),

        "itemName": (
            f"Inscription tournoi "
            f"{data['prenom']} {data['nom']}"
        ),

        "metadata": {
            "licence": str(data.get("licence", "")),
            "nom": data.get("nom", ""),
            "prenom": data.get("prenom", ""),
            "email": data.get("mail", ""),
            "club": data.get("club", ""),
            "points": str(data.get("points", "")),
            "tableaux": ",".join(data.get("tableaux", []))
        },

        "backUrl": "https://tournoi-thuir.up.railway.app",
        "errorUrl": "https://tournoi-thuir.up.railway.app",
        "returnUrl": "https://tournoi-thuir.up.railway.app"
    }

    print("METADATA =", payload["metadata"])
    async with httpx.AsyncClient() as client:
        
        response = await client.post(
            f"https://api.helloasso.com/v5/organizations/{ORGANIZATION}/checkout-intents",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json=payload
        )

    if response.status_code >= 400:
        return {
            "status": response.status_code,
            "body": response.text
        }

    return response.json()

