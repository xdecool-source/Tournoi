# EXPORT_HOUR=20 l'export demarre à 20h00
# si a 20h00 le container tombe pas d'export sauf le lendemain 
# voila la limite !!!!
# railway run python mon script

import asyncio
import os

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services.admin_ex_mail import process_admin_export
from dotenv import load_dotenv

load_dotenv(".env", override=False)

EXPORT_HOUR = int(os.getenv("EXPORT_HOUR", 20))
EXPORT_MINUTE = int(os.getenv("EXPORT_MINUTE", 0))
EXPORT_ENABLED = os.getenv("EXPORT_ENABLED", "true").lower() == "true"

async def export_scheduler():
    
    if not EXPORT_ENABLED:
        print(" Scheduler désactivé via ENV")
        return

    tz = ZoneInfo("Europe/Paris")
    while True:
        now = datetime.now(tz)
        next_run = now.replace(
            hour=EXPORT_HOUR,
            minute=EXPORT_MINUTE,
            second=0,
            microsecond=0
        )

        # si l'heure est déjà passée aujourd'hui
        
        if next_run <= now:
            next_run += timedelta(days=1)
        sleep_seconds = (next_run - now).total_seconds()
        print(f"Prochain export prévu à {next_run}")
        await asyncio.sleep(sleep_seconds)
        print(" Lancement export admin")
        await process_admin_export()