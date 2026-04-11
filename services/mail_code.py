# envoie un code aléatoire pour inscription par mail 

import os
import random
import time
import httpx
import aiosmtplib

from dotenv import load_dotenv
from email.message import EmailMessage

#  Env

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")

#  Smtp (Dev)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

#  Brevo

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

#  Commun

FROM_EMAIL = os.getenv("FROM_EMAIL")
print("Env Valeur =", ENV)
print("Smtp host =", SMTP_HOST)
print("From Email =", FROM_EMAIL)

#  Stockages Codes

verification_codes = {}

# Génération code

def generate_code():
    return str(random.randint(100000, 999999))

def store_verification_code(email):

    now = time.time()
    if email in verification_codes:
        data = verification_codes[email]
        if now < data["expire"]:
            raise ValueError("Un code est déjà envoyé. Attendez 5 minutes.")
    code = generate_code()
    verification_codes[email] = {
        "code": code,
        "expire": now + 300
    }
    # print("Code généré pour", email, ":", code)
    return code

def verify_code(email, code):

    data = verification_codes.get(email)
    if not data:
        return False
    if time.time() > data["expire"]:
        del verification_codes[email]
        return False
    if data["code"] == code:
        del verification_codes[email]
        return True
    return False

# Smtp Dev

async def send_smtp_email(to_email, subject, html):

    print(" Smtp ")
    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("Votre client mail ne supporte pas HTML")
    msg.add_alternative(html, subtype="html")
    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True
    )
    print("Mail Smtp Envoyé")


# Brevo prod

async def send_brevo_email(to_email, subject, html):

    print("Brevo")
    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html
    }

    async with httpx.AsyncClient(timeout=20) as client:

        r = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            json=payload
        )
        print("Brevo Status", r.status_code)

# Routeur Mail 

async def send_email(to_email, subject, html):

    print("Mode Mail =", "Smtp" if ENV == "dev" else "Brevo")
    if ENV == "dev":
        await send_smtp_email(to_email, subject, html)
    else:
        await send_brevo_email(to_email, subject, html)