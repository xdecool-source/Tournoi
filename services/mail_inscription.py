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
from core.config import TABLEAUX, NOM_TOURNOI
from services.db import get_conn

#  Chargement environnement

load_dotenv(".env", override=False)
ENV = os.getenv("ENV", "dev")

#  Smtp (DEV / LOCAL)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

#  Brevo (Production)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

#  Identique

FROM_EMAIL = os.getenv("FROM_EMAIL")
SITE_URL = os.getenv("SITE_URL")

env = Environment(loader=FileSystemLoader("userinterface/templates"))

#  Construction HTML email

async def build_email_html(data: dict, type_mail: str):
    # print("DATA TABLEAUX:", data["tableaux"])
    reste_inscriptions = None
    template_map = {
        "creation": "email_creation.html",
        "modification": "email_modification.html",
        "suppression": "email_suppression.html"
    }

    template_name = template_map.get(type_mail, "email_creation.html")
    
    #  print(" 1 - chargement template")
    
    template = env.get_template(template_name)
    
    if type_mail == "suppression":
        html_content = template.render(
            prenom=data["prenom"],
            nom=data["nom"],
            licence=data["licence"],
            club=data.get("club", ""),
            points=data.get("points", ""),
            tableaux="Aucun tableau sélectionné",
            site_url=SITE_URL,
            NOM_TOURNOI=NOM_TOURNOI,
            reste_inscriptions=reste_inscriptions,
            FROM_EMAIL=FROM_EMAIL   
        )
        return html_content
    
    #  print(" 2 - construction tableaux")
    
    tableaux_details = []
    tableaux_str = ""   # 🔥 AJOUT ICI
    total_html = ""     # 🔥 AJOUT ICI
    
    async with get_conn() as conn:

        # 🔥 TOTAL GLOBAL (tous les jours)
        rows = await conn.fetch("""
            SELECT tableau
            FROM inscription_tableaux
            WHERE licence=$1
        """, data["licence"])
        
        reste_inscriptions = len(rows) > 0
        total = sum(
            TABLEAUX.get(r["tableau"], {}).get("prix", 0)
            for r in rows
        )

        # 🔁 détails du jour
        event_id = data.get("event_id", 1)

        for t in data["tableaux"]:
            # print("BOUCLE T:", t) 
            # print("CONF:", TABLEAUX.get(t))
            
            conf = TABLEAUX.get(t, {})
            prix = conf.get("prix", 0)

            min_pts = conf.get("min")
            max_pts = conf.get("max")

            statut = await conn.fetchval(
                """
                SELECT statut
                FROM inscription_tableaux
                WHERE licence=$1 AND tableau=$2 AND event_id=$3
                """,
                data["licence"],
                t,
                event_id
            )

            if statut == "OK":
                statut_txt = "✅ Confirmé"
            elif statut == "ATTENTE":
                statut_txt = "⏳ Liste d'attente"
            else:
                statut_txt = "🔒 Non validé"

            nom = conf.get("label", t)
            prix = conf.get("prix", 0)
            jour = conf.get("jour", {}).get("label", "")
            
            if min_pts is None and max_pts is None:
                ligne = f"{nom} ({jour}) — {prix}€ {statut_txt}"
            else:
                ligne = f"{nom} ({min_pts}-{max_pts} pts, {jour}) — {prix}€ {statut_txt}"

            # print("LIGNE:", ligne)

            tableaux_details.append(ligne) 

            tableaux_str = "<br>".join(tableaux_details)
            total_html = f"<br><br>💰 Total : {total}€"
                
    
    #  print(" 3 - render HTML")
    
    jour = "Samedi" if event_id == 1 else "Dimanche"
    
    html_content = template.render(
        prenom=data["prenom"],
        nom=data["nom"],
        licence=data["licence"],
        club=data.get("club", ""),
        points=data.get("points", ""),
        tableaux=tableaux_str + total_html, 
        site_url=SITE_URL,
        jour=jour,
        NOM_TOURNOI=NOM_TOURNOI,
        reste_inscriptions=reste_inscriptions,
        FROM_EMAIL=FROM_EMAIL   
    )
    return html_content

#  Envoi SMTP (Dev)

async def send_smtp_email(to_email: str, subject: str, html_content: str):
    
    #  print(" 4 - envoi SMTP")
    
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
        # print(" Mail Smtp Envoyé")
    except Exception as e:
        print(" Erreur Smtp :", e)

#  Envoi Brevo (Production)

async def send_brevo_email(to_email: str, subject: str, html_content: str):

    #  print(" 4 - envoi Brevo")
    
    payload = {
        "sender": {"email": FROM_EMAIL},
        "to": [{"email": to_email}],
        # "cc": [{"email": ADMIN_EMAIL}] if ADMIN_EMAIL else [],
        "subject": subject,
        "htmlContent": html_content,
    }
    # print("Brevo Api key =", BREVO_API_KEY)
    # print("From Email =", FROM_EMAIL)
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

#  Fonction principale

async def send_confirmation_email(to_email: str, data: dict, type_mail: str):

    html_content = await build_email_html(data, type_mail)
    
    if type_mail == "creation":
        subject = f"Confirmation d'inscription - Tournoi {NOM_TOURNOI}"
    elif type_mail == "modification":
        subject = f"Modification d'inscription - Tournoi {NOM_TOURNOI}"
    elif type_mail == "suppression":
        subject = f"Annulation d'inscription - Tournoi {NOM_TOURNOI}"
    else:
        subject = f"Tournoi {NOM_TOURNOI}"
        
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
        
#  Fonction générique envoi de mail

async def send_email(to_email: str, subject: str, html_content: str):

    if ENV != "dev":
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
        
    