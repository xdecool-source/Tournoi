# Génere fichier excel inscription en mode batch 
# donc a la demande 

import asyncio

from services.db import init_db_pool, init_db
from export.generate_inscription import generate

async def main():

    await init_db_pool()   # crée la connexion PostgreSQL
    await init_db()        # crée les tables si besoin
    await generate()       # génère l'excel
    print("Excel généré")
asyncio.run(main())

