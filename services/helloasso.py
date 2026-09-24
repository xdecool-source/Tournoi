import os
import time
import asyncio
import httpx

from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("HELLOASSO_CLIENT_ID")
CLIENT_SECRET = os.getenv("HELLOASSO_CLIENT_SECRET")

HELLOASSO_AUTH = os.getenv("HELLOASSO_AUTH")
HELLOASSO_API = os.getenv("HELLOASSO_API")
HELLOASSO_BACK_URL = os.getenv("HELLOASSO_BACK_URL")
HELLOASSO_ERROR_URL = os.getenv("HELLOASSO_ERROR_URL")
HELLOASSO_RETURN_URL = os.getenv("HELLOASSO_RETURN_URL")
ORGANIZATION = os.getenv("ORGANIZATION")

TIMEOUT = httpx.Timeout(
    connect=10,
    read=30,
    write=30,
    pool=30,
)


class HelloAssoClient:

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expire = 0

        self.token_lock = asyncio.Lock()

    async def get_token(self, force_refresh=False):

        now = time.time()

        if (
            not force_refresh
            and self.access_token
            and now < self.token_expire - 60
        ):
            return self.access_token

        async with self.token_lock:

            now = time.time()

            if (
                not force_refresh
                and self.access_token
                and now < self.token_expire - 60
            ):
                return self.access_token

            for tentative in range(3):

                try:

                    async with httpx.AsyncClient(
                        timeout=TIMEOUT
                    ) as client:

                        if not self.refresh_token:

                            response = await client.post(
                                HELLOASSO_AUTH,
                                data={
                                    "grant_type":
                                        "client_credentials",
                                    "client_id":
                                        CLIENT_ID,
                                    "client_secret":
                                        CLIENT_SECRET,
                                },
                            )

                        else:

                            response = await client.post(
                                HELLOASSO_AUTH,
                                data={
                                    "grant_type":
                                        "refresh_token",
                                    "refresh_token":
                                        self.refresh_token,
                                },
                            )

                    response.raise_for_status()

                    data = response.json()

                    self.access_token = data[
                        "access_token"
                    ]

                    if data.get("refresh_token"):
                        self.refresh_token = data[
                            "refresh_token"
                        ]

                    expires_in = int(
                        data.get(
                            "expires_in",
                            1800,
                        )
                    )

                    self.token_expire = (
                        time.time()
                        + expires_in
                    )

                    return self.access_token

                except (
                    httpx.ReadTimeout,
                    httpx.ConnectTimeout,
                    httpx.ConnectError,
                ):

                    if tentative == 2:
                        raise

                    await asyncio.sleep(
                        2 ** tentative
                    )

    async def create_checkout(
        self,
        montant,
        data,
    ):

        # montant = euros
        # HelloAsso reçoit des centimes

        montant_centimes = int(
            round(float(montant) * 100)
        )

        payload = {
            "totalAmount": montant_centimes,
            "initialAmount": montant_centimes,

            "itemName":
                f"{data['nom']} "
                f"{data['prenom']} "
                f"- Licence {data['licence']} "
                f"- "
                f"{','.join(data['tableaux'])}",

            "containsDonation": False,

            "payer": {
                "lastName":
                    data["nom"],

                "firstName":
                    data["prenom"],

                "email":
                    data["mail"].lower(),
            },

            "metadata": {
                "type":
                    data.get(
                        "type",
                        "inscription",
                    ),

                "licence":
                    str(data["licence"]),

                "nom":
                    data["nom"],

                "prenom":
                    data["prenom"],

                "email":
                    data["mail"],

                "club":
                    data.get("club", ""),

                "points":
                    str(
                        data.get(
                            "points",
                            "",
                        )
                    ),

                "tableaux":
                    ",".join(
                        data["tableaux"]
                    ),

                # Utilisé uniquement
                # lors d'une modification
                "modification_id":
                    str(
                        data.get(
                            "modification_id",
                            "",
                        )
                    ),
            },

            "backUrl":
                HELLOASSO_BACK_URL,

            "errorUrl":
                HELLOASSO_ERROR_URL,

            "returnUrl":
                HELLOASSO_RETURN_URL,
        }

        for tentative in range(3):

            token = await self.get_token()

            try:

                async with httpx.AsyncClient(
                    timeout=TIMEOUT
                ) as client:

                    response = await client.post(
                        (
                            f"{HELLOASSO_API}"
                            f"/v5/organizations/"
                            f"{ORGANIZATION}"
                            f"/checkout-intents"
                        ),
                        headers={
                            "Authorization":
                                f"Bearer {token}"
                        },
                        json=payload,
                    )

                if response.status_code == 401:

                    await self.get_token(
                        force_refresh=True
                    )

                    continue

                response.raise_for_status()

                return response.json()

            except (
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.ConnectError,
            ):

                if tentative == 2:
                    raise

                await asyncio.sleep(
                    2 ** tentative
                )

            except httpx.HTTPStatusError as e:

                print(
                    "Erreur HelloAsso :",
                    e.response.status_code,
                )

                print(
                    e.response.text
                )

                raise

        raise RuntimeError(
            "Impossible de créer le paiement HelloAsso"
        )


helloasso = HelloAssoClient()


async def create_checkout(
    montant,
    data,
):
    return await helloasso.create_checkout(
        montant=montant,
        data=data,
    )


async def test_helloasso():

    token = await helloasso.get_token()

    print(
        "ACCESS TOKEN :",
        token[:20] + "...",
    )

    print(
        "REFRESH TOKEN :",
        (
            helloasso.refresh_token[:20] + "..."
            if helloasso.refresh_token
            else None
        ),
    )
    