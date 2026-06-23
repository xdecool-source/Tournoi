import os
import httpx

from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("HELLOASSO_CLIENT_ID")
CLIENT_SECRET = os.getenv("HELLOASSO_CLIENT_SECRET")

async def get_token():

    async with httpx.AsyncClient() as client:
        response = await client.post(
            # "https://api.helloasso.com/oauth2/token",
            "https://api.helloasso-sandbox.com/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
        )
        
    response.raise_for_status()
    data = response.json()
    return data["access_token"]

# ORGANIZATION = "tennis-de-table-thuirinois"
ORGANIZATION = "test-tt-thuir"

HELLOASSO_CARTE = os.getenv("HELLOASSO_CARTE", "true").lower() == "true"

async def create_checkout(montant, data):

    if not HELLOASSO_CARTE:
        raise RuntimeError("HelloAsso désactivé")
    
    token = await get_token()
    payload = {
        "totalAmount": int(montant * 100),
        "initialAmount": int(montant * 100),
        
        "itemName": (
            f"{data['prenom']} {data['nom']} "
            f"- Licence {data['licence']} "
            f"- {','.join(data['tableaux'])}"
        ),
        
        "containsDonation": False,
        
        "payer": {
            "firstName": str(data.get("prenom", "")).strip(),
            "lastName": str(data.get("nom", "")).strip(),
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
        
        "backUrl": "https://tournoi-thuir.up.railway.app",
        "errorUrl": "https://tournoi-thuir.up.railway.app",
        "returnUrl": "https://tournoi-thuir.up.railway.app"
         
    }
    
    async with httpx.AsyncClient() as client:
        
        response = await client.post(
            # f"https://api.helloasso.com/v5/organizations/{ORGANIZATION}/checkout-intents",
            f"https://api.helloasso-sandbox.com/v5/organizations/{ORGANIZATION}/checkout-intents",
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

