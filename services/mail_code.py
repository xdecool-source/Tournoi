# envoie un code aléatoire pour inscription par mail 

import os
import random
import time
import httpx
import aiosmtplib
import psycopg2
import secrets

from dotenv import load_dotenv
from email.message import EmailMessage

#  Env

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")
DATABASE_URL = os.getenv("DATABASE_URL")

#  Smtp (Dev)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

#  Brevo

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

#  Commun

FROM_EMAIL = os.getenv("FROM_EMAIL")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL")
# print("Env Valeur =", ENV)
# print("Smtp host =", SMTP_HOST)
# print("From Email =", FROM_EMAIL)

#  Stockages Codes

verification_codes = {}
# print("MAIL_CODE CHARGE")
# Génération code

def generate_code():
    return f"{secrets.randbelow(900000) + 100000}"

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
    # reveil database
    # import asyncio

    reveil_database() 
    # print("Code généré pour", email, ":", code)
    return code

def verify_code(email, code):

    # print("AVANT VERIFY =", verification_codes)
    data = verification_codes.get(email)
    if not data:
        # print("AUCUN CODE")
        return False
    # expiration
    if time.time() > data["expire"]:
        del verification_codes[email]
        # print("EXPIRE")
        return False
    # mauvais code
    if data["code"] != code:
        # print("MAUVAIS CODE")
        return False
    # SUCCESS
    del verification_codes[email]
    # print("SUPPRIME =", verification_codes)
    return True

# Smtp Dev

async def send_smtp_email(to_email, subject, html):

    msg = EmailMessage()
    msg["From"] = f"Tournoi <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = REPLY_TO_EMAIL
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

    payload = {
        "sender": {
            "name": "Tournoi",
            "email": FROM_EMAIL
        },
        "to": [
            {"email": to_email}
        ],
        "replyTo": {
            "email": REPLY_TO_EMAIL,
            "name": "Tournoi"
        },
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
        # print("Brevo Status pour le code mail", r.status_code)
        r.raise_for_status()
        
# Reveil database Neon
    
def reveil_database():

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        print("DB réveillée")
    except Exception as e:
        print("Erreur DB:", e)

# Routeur Mail 

async def send_email(to_email, subject, html):
    
    print("Mode Mail =", "Smtp" if ENV == "dev" else "Brevo")
    if ENV == "dev":
        await send_smtp_email(to_email, subject, html)
    else:
        await send_brevo_email(to_email, subject, html)