# Génere fichier excel inscription et l'envoie par mail
# Mode batch en local sur Pc

import asyncio
import os
import base64
import httpx
from email.message import EmailMessage
import aiosmtplib

from dotenv import load_dotenv
from services.db import init_db_pool, init_db
from export.generate_inscription import generate

# Chargement environnement

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")
print("MAIL MODE =", ENV)

# Smtp (Dev / Local)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Brevo (Production)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# Commun

FROM_EMAIL = os.getenv("FROM_EMAIL")
SITE_URL = os.getenv("SITE_URL")

# Envoi  Smtp

async def send_smtp_email(msg):

    #  print("envoi SMTP")
    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True
    )
    #  print("SMTP mail envoyé")

# Envoi Brevo 

async def send_brevo_email(to_email, subject, html_content, excel_stream):

    #  print(" envoi BREVO")
    
    attachment = base64.b64encode(excel_stream.read()).decode()
    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "cc": [{"email": ADMIN_EMAIL}] if ADMIN_EMAIL else [],
        "subject": subject,
        "htmlContent": html_content,
        "attachment": [
            {
                "content": attachment,
                "name": "Inscriptions.xlsx"
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
        print("Brevo status:", response.status_code)
        print("Brevo response:", response.text)
        response.raise_for_status()



# Routeur Mail 

async def send_email(excel_stream):

    subject = "Export inscriptions tournoi"
    html = "<h3>Fichier Excel des inscriptions en pièce jointe</h3>"
    if ENV == "production":
        await send_brevo_email(
            ADMIN_EMAIL,
            subject,
            html,
            excel_stream
        )

    else:

        msg = EmailMessage()
        msg["From"] = FROM_EMAIL
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = subject
        msg.set_content("Fichier Excel des inscriptions en pièce jointe")
        msg.add_attachment(
            excel_stream.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="Inscriptions.xlsx"
        )
        await send_smtp_email(msg)


# Main 

async def main():

    await init_db_pool()
    await init_db()

    # génération Excel
    
    excel_stream = generate()
    if not excel_stream:
        print("Aucun fichier généré")
        return
    print("Excel généré")
    await send_email(excel_stream)
    print("Mail envoyé")

# Run

asyncio.run(main())
