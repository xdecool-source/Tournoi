"""
get_token()
authentifie auprès de HelloAsso avec
HELLOASSO_CLIENT_ID
HELLOASSO_CLIENT_SECRET
et récupère un jeton OAuth2 (access_token).

create_checkout()
fonction construit une demande de paiement.
envoie à HelloAsso :

le montant 
le nom du joueur 
son email 
sa licence 
ses tableaux 
les URL de retour (backUrl, returnUrl, errorUrl).

"""

import os
import httpx
import asyncio

from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("HELLOASSO_CLIENT_ID")
CLIENT_SECRET = os.getenv("HELLOASSO_CLIENT_SECRET")
HELLOASSO_CARTE = os.getenv("HELLOASSO_CARTE", "true").lower() == "true"
HELLOASSO_AUTH = os.getenv("HELLOASSO_AUTH")
HELLOASSO_BACK_URL = os.getenv("HELLOASSO_BACK_URL")
HELLOASSO_ERROR_URL = os.getenv("HELLOASSO_ERROR_URL")
HELLOASSO_RETURN_URL = os.getenv("HELLOASSO_RETURN_URL")
HELLOASSO_API = os.getenv("HELLOASSO_API")
ORGANIZATION = os.getenv("ORGANIZATION")

async def get_token():
    timeout = httpx.Timeout(connect=10, read=30, write=30, pool=30)

    for tentative in range(3):  # 3 essais
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    HELLOASSO_AUTH,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                    },
                )

            response.raise_for_status()
            return response.json()["access_token"]

        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            print(f"Tentative {tentative + 1}/3 échouée : {e}")

            if tentative == 2:
                raise

            # Attendre 1 s, puis 2 s
            await asyncio.sleep(2 ** tentative)

async def create_checkout(montant, data):

    if not HELLOASSO_CARTE:
        raise RuntimeError("HelloAsso désactivé")
    
    token = await get_token()
    payload = {
        
        "totalAmount": int(montant * 100),
        "initialAmount": int(montant * 100),
        "itemName": (
            f"{data['nom']} {data['prenom']}  "
            f"- Licence {data['licence']} "
            f"- {','.join(data['tableaux'])}"
        ),
        "containsDonation": False,
        "payer": {
            "lastName": str(data.get("nom", "")).strip(),
            "firstName": str(data.get("prenom", "")).strip(),
            "email": str(data.get("mail", "")).strip().lower()
        },
        "metadata": {
            "licence": data.get("licence", ""),
            "nom": data.get("nom", ""),
            "prenom": data.get("prenom", ""),
            "email": data.get("mail", ""),
            "club": data.get("club", ""), 
            "points": str(data.get("points", "")),
            "tableaux": ",".join(data.get("tableaux", []))
        },
        "backUrl": HELLOASSO_BACK_URL,
        "errorUrl": HELLOASSO_ERROR_URL,
        "returnUrl": HELLOASSO_RETURN_URL
    }
    
    timeout = httpx.Timeout(connect=10, read=30, write=30, pool=30)

    for tentative in range(3):
        try:
            token = await get_token()

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{HELLOASSO_API}/v5/organizations/{ORGANIZATION}/checkout-intents",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    json=payload
                )

            response.raise_for_status()
            return response.json()

        except (httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.ConnectError) as e:

            print(f"Checkout tentative {tentative + 1}/3 : {e}")

            if tentative == 2:
                raise

            await asyncio.sleep(2 ** tentative)

        except httpx.HTTPStatusError as e:
            print(f"Erreur HTTP {e.response.status_code}")
            print(e.response.text)

            # Si erreur métier (400, 403, etc.), inutile de réessayer
            raise
        
