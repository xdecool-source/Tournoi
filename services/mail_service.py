import os
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from core.config import TABLEAUX
from services.db import get_conn


if os.getenv("ENV") != "production":
    load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
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

    # 🔹 Construction des tableaux avec statut réel
    tableaux_details = []

    async with get_conn() as conn:
        for t in data["tableaux"]:

            conf = TABLEAUX.get(t, {})
            min_pts = conf.get("min")
            max_pts = conf.get("max")

            min_pts = min_pts if min_pts is not None else "Non défini"
            max_pts = max_pts if max_pts is not None else "Non défini"

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

    message = EmailMessage()
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Cc"] = ADMIN_EMAIL

    message["Subject"] = (
        "Confirmation d'inscription - Tournoi"
        if type_mail == "creation"
        else "Modification d'inscription - Tournoi"
    )

    message.set_content("Votre client mail ne supporte pas le HTML.")
    message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )