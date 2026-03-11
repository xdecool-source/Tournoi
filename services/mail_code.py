# services/mail_service.py
# Gestion du mail pour le code de validation en saisie

import random
import os
import httpx
import aiosmtplib
import time

from dotenv import load_dotenv
from email.message import EmailMessage
from core.config import TABLEAUX
from services.db import get_conn

# ------------ Chargement environnement

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

verification_codes = {}

# ---------------  GENERATION CODE

def generate_code():
    return str(random.randint(100000, 999999))

def store_verification_code(email):

    now = time.time()
    print("DICT ACTUEL:", verification_codes)
    if email in verification_codes:
        data = verification_codes[email]
        if now < data["expire"]:
            raise ValueError("Un code est déjà envoyé. Attendez 10 minutes.")
    code = generate_code()
    verification_codes[email] = {
        "code": code,
        "expire": now + 300  # ---- 5 minutes 
    }
    print(f"Code généré pour {email} : {code}")
    return code

def verify_code(email, code):

    data = verification_codes.get(email)
    if not data:
        return False
    if time.time() > data["expire"]:
        del verification_codes[email]
        return False
    if data["code"] == code:
        del verification_codes[email]   # supprime le code utilisé
        return True
    return False

# --------------- ENVOI EMAIL SMTP

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

# ------------  ENVOI EMAIL BREVO

async def send_brevo_email(to_email: str, subject: str, html_content: str):

    print("STEP 4 - envoi BREVO")
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print("✅ MAIL BREVO ENVOYÉ")
        else:
            print("❌ ERREUR BREVO :", response.text)

# ------- FONCTION PRINCIPALE

async def send_confirmation_email(to_email: str, html_content: str, type_mail: str):
    subject = (
        "Confirmation d'inscription - Tournoi Homopongistus"
        if type_mail == "creation"
        else "Modification d'inscription - Tournoi Homopongistus"
    )
    if ENV == "prod":
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