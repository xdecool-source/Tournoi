import os
import time
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("HELLOASSO_CLIENT_ID")
CLIENT_SECRET = os.getenv("HELLOASSO_CLIENT_SECRET")

HELLOASSO_CARTE = os.getenv("HELLOASSO_CARTE", "true").lower() == "true"
HELLOASSO_AUTH = os.getenv("HELLOASSO_AUTH")
HELLOASSO_API = os.getenv("HELLOASSO_API")
HELLOASSO_BACK_URL = os.getenv("HELLOASSO_BACK_URL")
HELLOASSO_ERROR_URL = os.getenv("HELLOASSO_ERROR_URL")
HELLOASSO_RETURN_URL = os.getenv("HELLOASSO_RETURN_URL")
ORGANIZATION = os.getenv("ORGANIZATION")

TIMEOUT = httpx.Timeout(connect=10, read=30, write=30, pool=30)

# Cache du token
_token = None
_token_expire = 0


async def get_token(force_refresh=False):
    """
    Retourne un token OAuth HelloAsso.

    - utilise le cache
    - renouvelle automatiquement le token avant expiration
    - retry automatique si timeout
    """

    global _token, _token_expire

    now = time.time()

    if (
        not force_refresh
        and _token is not None
        and now < _token_expire - 60
    ):
        return _token

    for tentative in range(3):

        try:

            async with httpx.AsyncClient(timeout=TIMEOUT) as client:

                response = await client.post(
                    HELLOASSO_AUTH,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                    },
                )

            response.raise_for_status()

            data = response.json()

            _token = data["access_token"]

            expires_in = data.get("expires_in", 3600)

            _token_expire = now + expires_in

            print("Nouveau token HelloAsso obtenu")

            return _token

        except (
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.ConnectError,
        ) as e:

            print(f"Timeout HelloAsso ({tentative+1}/3) : {e}")

            if tentative == 2:
                raise

            await asyncio.sleep(2 ** tentative)
            
            
async def create_checkout(montant, data):

    if not HELLOASSO_CARTE:
        raise RuntimeError("HelloAsso désactivé")

    payload = {

        "totalAmount": int(montant * 100),
        "initialAmount": int(montant * 100),

        "itemName":
            f"{data['nom']} {data['prenom']} "
            f"- Licence {data['licence']} "
            f"- {','.join(data['tableaux'])}",

        "containsDonation": False,

        "payer": {
            "lastName": data["nom"],
            "firstName": data["prenom"],
            "email": data["mail"].lower(),
        },

        "metadata": {
            "licence": data["licence"],
            "nom": data["nom"],
            "prenom": data["prenom"],
            "email": data["mail"],
            "club": data.get("club", ""),
            "points": str(data.get("points", "")),
            "tableaux": ",".join(data["tableaux"]),
        },

        "backUrl": HELLOASSO_BACK_URL,
        "errorUrl": HELLOASSO_ERROR_URL,
        "returnUrl": HELLOASSO_RETURN_URL,
    }

    for tentative in range(3):

        try:

            token = await get_token()

            async with httpx.AsyncClient(timeout=TIMEOUT) as client:

                response = await client.post(
                    f"{HELLOASSO_API}/v5/organizations/{ORGANIZATION}/checkout-intents",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                    json=payload,
                )

            # Token expiré → on le renouvelle puis on recommence
            if response.status_code == 401:

                print("Token expiré → renouvellement")

                await get_token(force_refresh=True)

                continue

            response.raise_for_status()

            return response.json()

        except (
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.ConnectError,
        ) as e:

            print(f"Erreur réseau ({tentative+1}/3) : {e}")

            if tentative == 2:
                raise

            await asyncio.sleep(2 ** tentative)

        except httpx.HTTPStatusError:

            print(response.status_code)
            print(response.text)

            raise
        
        
