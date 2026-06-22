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

ORGANIZATION = "tennis-de-table-thuirinois"



async def create_checkout(montant, licence):

    token = await get_token()

    payload = {
        "totalAmount": int(montant * 100),
        "initialAmount": int(montant * 100),
        "itemName": f"Inscription tournoi licence {licence}",
        "backUrl": "https://tournoi-thuir.up.railway.app",
        "errorUrl": "https://tournoi-thuir.up.railway.app",
        "returnUrl": "https://tournoi-thuir.up.railway.app"
    }

    print("payload =", payload)
    async with httpx.AsyncClient() as client:
        
        response = await client.post(
            f"https://api.helloasso.com/v5/organizations/{ORGANIZATION}/checkout-intents",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json=payload
        )
        print("STATUS =", response.status_code)
    
    if response.status_code >= 400:
        print("HELLOASSO ERROR =", response.text)
        return {
            "status": response.status_code,
            "body": response.text
        }

    data = response.json()
    print("HELLOASSO RESPONSE =", data)

    return data
