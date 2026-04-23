# récupère les inscriptions en base
# crée un fichier Excel
# le garde en mémoire (pas de fichier disque)
# crée un email
# ajoute l’Excel en pièce jointe
# envoie via serveur SMTP
# encode le fichier en base64
# appelle l’API Brevo"
# envoie l’email avec pièce jointe

from export.generate_inscription import generate
from services.db import should_send_admin_mail, update_admin_mail_status, get_conn
from email.message import EmailMessage
from dotenv import load_dotenv

import aiosmtplib
import httpx
import os
import base64

# Chargement environnement
load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")

# SMTP (Dev / Local)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Brevo (Production)
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# Commun
FROM_EMAIL = os.getenv("FROM_EMAIL")

# SMTP Dev
async def send_smtp_email(excel_stream):

    # print("envoi SMTP")
    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = "Export inscriptions tournoi"
    msg.set_content("Fichier Excel en pièce jointe")

    msg.add_attachment(
        excel_stream.getvalue(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Inscriptions.xlsx"
    )

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )
    # print("MAIL SMTP ENVOYÉ")

# Brevo Prod
async def send_brevo_email(excel_stream):

    # print("envoi BREVO")
    excel_stream.seek(0)
    encoded_file = base64.b64encode(
        excel_stream.read()
    ).decode()

    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": ADMIN_EMAIL}],
        "subject": "Export inscriptions tournoi",
        "htmlContent": "<p>Fichier Excel en pièce jointe</p>",
        "attachment": [
            {
                "name": "Inscriptions.xlsx",
                "content": encoded_file
            }
        ]
    }

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
        # print("Brevo status:", response.status_code)
        # print("Brevo response:", response.text)
        response.raise_for_status()
    # print("MAIL BREVO ENVOYÉ")

# Export admin

async def process_admin_export():
    async with get_conn() as conn:

        try:
            # print("Génération Excel")
            excel_stream = generate()
            if not excel_stream:
                print("Erreur génération Excel")
                return
            print("Excel généré")

            # envoi
            
            if ENV == "production":
                await send_brevo_email(excel_stream)
            else:
                await send_smtp_email(excel_stream)
            print("Export admin terminé")
            
        except Exception as e:
            print(f"Erreur export admin: {e}")