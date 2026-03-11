# envoie un mail de confirmation d’inscription.
# charge un template Jinja2
# récupère les tableaux choisis
# vérifie leur statut en base de données (OK / attente / refus)
# Choisit comment envoyer le mail
# SMTP en dev/local
# API Brevo en production
# Envoie le mail au joueur et avec copie à l’admin


import os
import httpx
import aiosmtplib

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage
from core.config import TABLEAUX
from services.db import get_conn

# ------------- Chargement environnement

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")

# ------------ SMTP (DEV / LOCAL)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# ------------ BREVO (PRODUCTION)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# ------------ IDENTIQUE

FROM_EMAIL = os.getenv("FROM_EMAIL")
SITE_URL = os.getenv("SITE_URL")

env = Environment(loader=FileSystemLoader("templates"))

# ------------ Construction HTML email

async def build_email_html(data: dict, type_mail: str):

    template_name = (
        "email_creation.html"
        if type_mail == "creation"
        else "email_modification.html"
    )

    print("STEP 1 - chargement template")
    template = env.get_template(template_name)
    print("STEP 2 - construction tableaux")
    tableaux_details = []
    async with get_conn() as conn:
        for t in data["tableaux"]:
            conf = TABLEAUX.get(t, {})
            min_pts = conf.get("min")
            max_pts = conf.get("max")
            statut = await conn.fetchval(
                """
                SELECT statut
                FROM inscription_tableaux
                WHERE licence=$1 AND tableau=$2
                """,
                data["licence"],
                t
            )

            if statut == "OK":
                statut_txt = "✅ Confirmé"
            elif statut == "ATTENTE":
                statut_txt = "⏳ Liste d'attente"
            else:
                statut_txt = "🔒 Non validé"
            if min_pts is None and max_pts is None:
                ligne = f"{t} {statut_txt}"
            else:
                min_aff = min_pts if min_pts is not None else "x"
                max_aff = max_pts if max_pts is not None else "x"
                ligne = f"{t} ({min_aff}-{max_aff} pts) — {statut_txt}"
            tableaux_details.append(ligne)
    tableaux_str = "<br>".join(tableaux_details)
    print("STEP 3 - render HTML")
    
    html_content = template.render(
        prenom=data["prenom"],
        nom=data["nom"],
        licence=data["licence"],
        club=data.get("club", ""),
        points=data.get("points", ""),
        tableaux=tableaux_str,
        site_url=SITE_URL
    )
    return html_content

# ------------ Envoi SMTP (DEV)

async def send_smtp_email(to_email: str, subject: str, html_content: str):
    print("STEP 4 - envoi SMTP")
    message = EmailMessage()
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("Votre client mail ne supporte pas le HTML.")
    message.add_alternative(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            start_tls=True,
        )
        print("✅ MAIL SMTP ENVOYÉ")
    except Exception as e:
        print("❌ ERREUR SMTP :", e)

# ------------ Envoi BREVO (PROD)

async def send_brevo_email(to_email: str, subject: str, html_content: str):

    print("STEP 4 - envoi BREVO")
    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "cc": [{"email": ADMIN_EMAIL}] if ADMIN_EMAIL else [],
        "subject": subject,
        "htmlContent": html_content,
    }
    print("BREVO_API_KEY =", BREVO_API_KEY)
    print("FROM_EMAIL =", FROM_EMAIL)
    async with httpx.AsyncClient(timeout=20) as client:

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

# ------------ Fonction principale

async def send_confirmation_email(to_email: str, data: dict, type_mail: str):

    html_content = await build_email_html(data, type_mail)
    subject = (
        "Confirmation d'inscription - Tournoi Homopongistus"
        if type_mail == "creation"
        else "Modification d'inscription - Tournoi Homopongistus"
    )
    if ENV == "production":
        await send_brevo_email(
            to_email,
            subject,
            html_content
        )
    else:
        await send_smtp_email(
            to_email,
            subject,
            html_content
        )