import os
import httpx
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from core.config import TABLEAUX
from services.db import get_conn

# Service mail protocol https 

# Charger .env uniquement en local
if os.getenv("ENV") == "development":
    load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
SITE_URL = os.getenv("SITE_URL")

env = Environment(loader=FileSystemLoader("templates"))

async def send_confirmation_email(to_email: str, data: dict, type_mail: str):

    template_name = (
        "email_creation.html"
        if type_mail == "creation"
        else "email_modification.html"
    )

    template = env.get_template(template_name)

    tableaux_details = []

    async with get_conn() as conn:
        for t in data["tableaux"]:
            conf = TABLEAUX.get(t, {})
            min_pts = conf.get("min")
            max_pts = conf.get("max")

            min_pts = min_pts if min_pts is not None else " - "
            max_pts = max_pts if max_pts is not None else " - "

            statut = await conn.fetchval("""
                SELECT statut
                FROM inscription_tableaux
                WHERE licence=$1 AND tableau=$2
            """, data["licence"], t)

            if statut == "OK":
                statut_txt = "✅ Confirmé"
            elif statut == "ATTENTE":
                statut_txt = "⏳ Liste d'attente"
            else:
                statut_txt = "🔒 Non validé"

            tableaux_details.append(
                f"{t} ({min_pts}-{max_pts} pts) — {statut_txt}"
            )

    tableaux_str = "<br>".join(tableaux_details)

    html_content = template.render(
        prenom=data["prenom"],
        nom=data["nom"],
        licence=data["licence"],
        club=data.get("club", ""),
        points=data.get("points", ""),
        tableaux=tableaux_str,
        site_url=SITE_URL
    )

    subject = (
        "Confirmation d'inscription - Tournoi Homopongistus"
        if type_mail == "creation"
        else "Modification d'inscription - Tournoi Homopongistus"
    )

    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "cc": [{"email": ADMIN_EMAIL}] if ADMIN_EMAIL else [],
        "subject": subject,
        "htmlContent": html_content,
    }
    print("BREVO_API_KEY =", BREVO_API_KEY)
    print("FROM_EMAIL =", FROM_EMAIL)
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json",
            },
            json=payload,
        )

        print("Brevo status:", response.status_code)
        print("Brevo response:", response.text)

        response.raise_for_status()