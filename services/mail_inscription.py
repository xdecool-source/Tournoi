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
from services.db import get_conn, log_email

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

#  Identique

FROM_EMAIL = os.getenv("FROM_EMAIL")
ORIGINE_EMAIL = os.getenv("ORIGINE_EMAIL")
SITE_URL = os.getenv("SITE_URL")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL")

NBRE_TABLEAU = os.getenv("NBRE_TABLEAU")
DATE_TOURNOI = os.getenv("DATE_TOURNOI")
DATE_TOURNOI_JOUR = os.getenv("DATE_TOURNOI_JOUR")
NOM_TOURNOI = os.getenv("NOM_TOURNOI")
HELLOASSO_CARTE = (os.getenv("HELLOASSO_CARTE", "true").lower() == "true")


env = Environment(loader=FileSystemLoader("userinterface/templates"))

#  Construction HTML email

async def build_email_html(data: dict, type_mail: str):
    # print("DATA TABLEAUX:", data["tableaux"])
    reste_inscriptions = None
    
    if type_mail == "creation":
        # print ("carte = ",HELLOASSO_CARTE )
        if HELLOASSO_CARTE:
            template_name = "email_creation_helloasso_carte.html"
        else:
            template_name = "email_creation.html"
    elif type_mail == "modification":
        template_name = "email_modification.html"
    elif type_mail == "suppression":
        template_name = "email_suppression.html"
    else:
        template_name = "email_creation.html"
    
    # print(" 1 - chargement template")
    
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
            DATE_TOURNOI=DATE_TOURNOI,
            DATE_TOURNOI_JOUR=DATE_TOURNOI_JOUR,
            reste_inscriptions=reste_inscriptions,
            FROM_EMAIL=FROM_EMAIL,
            ORIGINE_EMAIL=ORIGINE_EMAIL   
        )
        return html_content
    
    # print(" 2 - construction tableaux")
    
    tableaux_details = []
    tableaux_str = ""   
    total_html = ""  
    

    # TOTAL GLOBAL (tous les jours)
    async with get_conn() as conn:

        event_id = data.get("event_id", 1)

        rows = await conn.fetch("""
            SELECT tableau, statut, event_id
            FROM inscription_tableaux
            WHERE licence=$1
        """, data["licence"])

        reste_inscriptions = len(rows) > 0

        total = sum(
            TABLEAUX.get(r["tableau"], {}).get("prix", 0)
            for r in rows
        )

        statuts = {
            r["tableau"]: r["statut"]
            for r in rows
            if r["event_id"] == event_id
        }

        for t in data["tableaux"]:

            conf = TABLEAUX.get(t, {})

            min_pts = conf.get("min")
            max_pts = conf.get("max")

            statut = statuts.get(t)

            if statut == "OK":
                statut_txt = "✅ Confirmé"
            elif statut == "ATTENTE":
                statut_txt = "⏳ Liste d'attente"
            else:
                statut_txt = "🔒 Non validé"

            nom = conf.get("label", t)
            prix = conf.get("prix", 0)
            jour = conf.get("jour", {}).get("label", "")
            heure = conf.get("jour", {}).get("hour", "")

            if min_pts is None and max_pts is None:
                ligne = f"{t} ({nom}, {jour} à {heure}) — {prix}€ {statut_txt}"
            else:
                ligne = f"{nom} ({min_pts}-{max_pts} pts, {jour} à {heure}) — {prix}€ {statut_txt}"

            tableaux_details.append(ligne)

        tableaux_str = "<br>".join(tableaux_details)
        total_html = f"<br><br>💰 Total : {total}€"
        
        # print(" 3 - render HTML")
        
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
            DATE_TOURNOI=DATE_TOURNOI,
            DATE_TOURNOI_JOUR=DATE_TOURNOI_JOUR,
            reste_inscriptions=reste_inscriptions,
            FROM_EMAIL=FROM_EMAIL,
            ORIGINE_EMAIL=ORIGINE_EMAIL   
        )
        return html_content

#  Envoi SMTP (Dev)

async def send_smtp_email(to_email: str, subject: str, html_content: str):
    
    #  print(" 4 - envoi SMTP")
    
    message = EmailMessage()
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message["Reply-To"] = REPLY_TO_EMAIL
    message.set_content(
        "Confirmation d'inscription au tournoi. "
        "Si vous ne visualisez pas correctement ce message, "
        "contactez l'organisation."
    )
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

async def send_brevo_email(
    to_email: str,
    subject: str,
    html_content: str
):
    
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
        "htmlContent": html_content,
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
        response.raise_for_status()
        result = response.json()
        return result.get("messageId")


#  Fonction principale

async def send_confirmation_email(to_email: str, data: dict, type_mail: str):

    html_content = await build_email_html(data, type_mail)
    
    if type_mail == "creation":
        
        # print("HELLOASSO_CARTE =", HELLOASSO_CARTE)
        # print("TYPE_MAIL =", type_mail)
        if HELLOASSO_CARTE:
            subject = (
                f"Inscription et Paiement enregistrée - "
                f"Tournoi {NOM_TOURNOI}"
            )
        else:
            subject = (
                f"Confirmation d'inscription - "
                f"Tournoi {NOM_TOURNOI}"
            )
    elif type_mail == "modification":
        subject = f"Modification d'inscription - Tournoi {NOM_TOURNOI}"
    elif type_mail == "suppression":
        subject = f"Annulation d'inscription - Tournoi {NOM_TOURNOI}"
    else:
        subject = f"Tournoi {NOM_TOURNOI}"
            
    if ENV == "prod":

        message_id = await send_brevo_email(
            to_email,
            subject,
            html_content
        )

        await log_email(
            licence=data["licence"],
            email=to_email,
            type_mail=type_mail,
            event_id=data.get("event_id", 1),
            subject=subject,
            brevo_message_id=message_id
        )

    else:
        await send_smtp_email(
            to_email,
            subject,
            html_content
        )
        
        await log_email(
            licence=data["licence"],
            email=to_email,
            type_mail=type_mail,
            event_id=data.get("event_id", 1),
            subject=subject,
            brevo_message_id="SMTP_DEV"
        )
        
                        
#  Fonction générique envoi de mail

async def send_email(to_email: str, subject: str, html_content: str):

    # print("Mode Mail =", "Smtp" if ENV == "dev" else "Brevo")
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
        
    