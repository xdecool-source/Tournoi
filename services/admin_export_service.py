
# Il vérifie s’il faut générer le mail admin qui regarde dans la table mail_control
# et construit le fichier Excel 
# L'Envoie suivant l'algorithme :   si nbre inscrit a changé et que le dernier mail
# n'a pas était envoyé aujourd'hui : OK
# générer l’Excel
# envoyer le mail avec l’Excel


from export.generate_inscription import generate
from services.db import should_send_admin_mail, update_admin_mail_status, get_conn
from email.message import EmailMessage
import aiosmtplib
import os

async def process_admin_export():

    async with get_conn() as conn:

        current_count = await conn.fetchval(
            "SELECT COUNT(*) FROM inscriptions"
        )

        send_mail = await should_send_admin_mail(conn, current_count)

        if not send_mail:
            print("Pas d'export aujourd'hui")
            return

        print("Génération Excel")

        excel_stream =  generate()

        if not excel_stream:
            return

        msg = EmailMessage()

        msg["From"] = os.getenv("FROM_EMAIL")
        msg["To"] = os.getenv("ADMIN_EMAIL")
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
            hostname=os.getenv("SMTP_HOST"),
            port=int(os.getenv("SMTP_PORT")),
            username=os.getenv("SMTP_USER"),
            password=os.getenv("SMTP_PASS"),
            start_tls=True,
        )

        await update_admin_mail_status(conn, current_count)

        print("Export admin terminé")