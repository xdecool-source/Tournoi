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

    async with httpx.AsyncClient() as client:
        response = await client.post(
            HELLOASSO_AUTH,
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
        )
        
    response.raise_for_status()
    data = response.json()
    return data["access_token"]

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
    
    async with httpx.AsyncClient() as client:
        
        response = await client.post(
            f"{HELLOASSO_API}/v5/organizations/{ORGANIZATION}/checkout-intents",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json=payload
        )
    
    if response.status_code >= 400:
        print("HelloAsso Error =", response.text)
        return {
            "status": response.status_code,
            "body": response.text
        }
    checkout = response.json()
    # print("HelloAsso Réponse =", checkout)
    return checkout
