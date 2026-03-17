# envoie un code aléatoire pour inscription par mail 

import os
import random
import time
import httpx
import aiosmtplib

from dotenv import load_dotenv
from email.message import EmailMessage

# -------- ENV

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")

# -------- SMTP (DEV)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# -------- BREVO

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# -------- COMMUN

FROM_EMAIL = os.getenv("FROM_EMAIL")
print("ENV VALUE =", ENV)
print("SMTP_HOST =", SMTP_HOST)
print("FROM_EMAIL =", FROM_EMAIL)

# -------- STOCKAGE CODES

verification_codes = {}

# -----------------------------------
# GENERATION CODE
# -----------------------------------

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
    print("Code généré pour", email, ":", code)
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

# -----------------------------------
# SMTP DEV
# -----------------------------------

async def send_smtp_email(to_email, subject, html):

    print("STEP SMTP")
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
    print("MAIL SMTP ENVOYÉ")

# -----------------------------------
# BREVO PROD
# -----------------------------------

async def send_brevo_email(to_email, subject, html):

    print("STEP BREVO")
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
        print("BREVO STATUS", r.status_code)

# -----------------------------------
# ROUTEUR MAIL
# -----------------------------------

async def send_email(to_email, subject, html):

    print("MODE MAIL =", "SMTP" if ENV == "dev" else "BREVO")
    if ENV == "dev":
        await send_smtp_email(to_email, subject, html)
    else:
        await send_brevo_email(to_email, subject, html)