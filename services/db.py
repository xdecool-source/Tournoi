import asyncpg, os
import subprocess
from datetime import datetime
from core.config import TABLEAUX
from contextlib import asynccontextmanager
from dotenv import load_dotenv
if os.getenv("ENV") != "production":
    load_dotenv()
    
#     load_dotenv()  # charge le fichier .env

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
pool = None

# ----------- init pool
async def init_db_pool():
    global pool

    if DATABASE_URL and "localhost" in DATABASE_URL:
        # 🔹 Local (pas de SSL)
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5
        )
    else:
        # 🔹 Production (Scalingo → SSL obligatoire)
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            ssl="require"
        )

# ----------- init DB
async def init_db():
    async with pool.acquire() as conn:

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS inscriptions (
            id SERIAL PRIMARY KEY,
            licence TEXT UNIQUE,
            nom TEXT,
            prenom TEXT,
            club TEXT,
            points INTEGER,
            mail TEXT,
            date_inscription TIMESTAMP
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS inscription_tableaux (
            id SERIAL PRIMARY KEY,
            licence TEXT,
            tableau TEXT,
            statut TEXT,
            UNIQUE(licence, tableau)
        )
        """)
        
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS export_control (
            id INTEGER PRIMARY KEY,
            counter INTEGER NOT NULL DEFAULT 0,
            trigger_count INTEGER NOT NULL DEFAULT 5
        )
        """)
        
        # 🔹 Initialisation si vide
        await conn.execute("""
        INSERT INTO export_control (id, counter, trigger_count)
        VALUES (1, 0, 5)
        ON CONFLICT (id) DO NOTHING
        """)

# ----------- licence déjà inscrite
async def licence_exists(licence):
    async with pool.acquire() as conn:
        r = await conn.fetchrow(
            "SELECT 1 FROM inscriptions WHERE licence=$1",
            licence
        )
        return r is not None

# ----------- toutes inscriptions
async def get_all():
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT i.*, 
        COALESCE(STRING_AGG(it.tableau, ','),'') AS tableaux
        FROM inscriptions i
        LEFT JOIN inscription_tableaux it ON i.licence=it.licence
        GROUP BY i.id
        ORDER BY points DESC
        """)
        return [dict(r) for r in rows]

# ----------- classement par tableau
async def get_classement_par_tableau():
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT i.*, it.tableau, it.statut
        FROM inscriptions i
        JOIN inscription_tableaux it ON i.licence=it.licence
        ORDER BY i.points DESC
        """)
        classement = {}
        for r in rows:
            classement.setdefault(r["tableau"], []).append(dict(r))
        return classement

# ----------- comptage
async def count_tableau(t, statut=None):
    async with pool.acquire() as conn:
        if statut:
            return await conn.fetchval("""
                SELECT COUNT(*) FROM inscription_tableaux
                WHERE tableau=$1 AND statut=$2
            """, t, statut)
        return await conn.fetchval("""
            SELECT COUNT(*) FROM inscription_tableaux
            WHERE tableau=$1
        """, t)

async def count_tableau_attente(t):
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM inscription_tableaux
            WHERE tableau=$1 AND statut='ATTENTE'
        """, t)


# ----------- statut tableau
async def tableau_status(t):
    conf = TABLEAUX[t]
    used_ok = await count_tableau(t, "OK")
    used_att = await count_tableau_attente(t)
    if used_ok < conf["capacite"]:
        return "OK"
    if used_att < conf.get("attente", 0):
        return "ATTENTE"
    return "FULL"


# ----------- sauvegarde inscription
async def save_inscription(data):
    if await licence_exists(data["licence"]):
        raise ValueError("Licence déjà inscrite")

    async with pool.acquire() as conn:
        async with conn.transaction():   # ⭐ transaction globale

            # 1️⃣ insertion joueur
            await conn.execute("""
            INSERT INTO inscriptions
            (nom, prenom, club, points, date_inscription, licence, mail)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            """,
            data["nom"],
            data["prenom"],
            data["club"],
            int(data["points"]),
            datetime.now(),
            data["licence"],
            data["mail"]
            )

            # 2️⃣ insertion tableaux avec verrouillage
            for t in data["tableaux"]:

                # 🔒 verrouille les lignes de ce tableau
                await conn.execute("""
                SELECT 1 FROM inscription_tableaux
                WHERE tableau=$1
                FOR UPDATE
                """, t)

                conf = TABLEAUX[t]

                used_ok = await conn.fetchval("""
                    SELECT COUNT(*) FROM inscription_tableaux
                    WHERE tableau=$1 AND statut='OK'
                """, t)

                if used_ok < conf["capacite"]:
                    status = "OK"
                else:
                    used_att = await conn.fetchval("""
                        SELECT COUNT(*) FROM inscription_tableaux
                        WHERE tableau=$1 AND statut='ATTENTE'
                    """, t)

                    if used_att < conf.get("attente", 0):
                        status = "ATTENTE"
                    else:
                        raise ValueError(f"{t} complet")

                await conn.execute("""
                INSERT INTO inscription_tableaux
                (licence, tableau, statut)
                VALUES ($1,$2,$3)
                """,
                data["licence"],
                t,
                status
                )
            await check_and_trigger_export(conn)   
    
                
                

# ----------- promotion attente
async def promote_attente(t):
    async with pool.acquire() as conn:
        ok = await count_tableau(t, "OK")
        conf = TABLEAUX[t]
        if ok >= conf["capacite"]:
            return
        row = await conn.fetchrow("""
        SELECT licence FROM inscription_tableaux
        WHERE tableau=$1 AND statut='ATTENTE'
        ORDER BY id
        LIMIT 1
        """, t)

        if row:
            await conn.execute("""
            UPDATE inscription_tableaux
            SET statut='OK'
            WHERE licence=$1 AND tableau=$2
            """, row["licence"], t)

async def get_tableaux_by_licence(licence):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT tableau
        FROM inscription_tableaux
        WHERE licence=$1
        """, licence)
        return [r["tableau"] for r in rows]

# ----------- connexion transaction
@asynccontextmanager
async def get_conn():
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)



# ----------- 
async def check_and_trigger_export(conn):
    # 🔒 On verrouille la ligne pour éviter double déclenchement
    row = await conn.fetchrow("""
        SELECT counter, trigger_count
        FROM export_control
        WHERE id=1
        FOR UPDATE
    """)

    counter = row["counter"] + 1
    trigger = row["trigger_count"]

    if counter >= trigger:
        # reset compteur
        await conn.execute("""
            UPDATE export_control
            SET counter = 0
            WHERE id=1
        """)

        # lancement batch (non bloquant)
        subprocess.Popen(["run_export.bat"], shell=True)

    else:
        # incrément simple
        await conn.execute("""
            UPDATE export_control
            SET counter = $1
            WHERE id=1
        """, counter)