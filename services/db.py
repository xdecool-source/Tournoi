"""
connexion PostgreSQL
création des tables multi-jour
gestion des inscriptions
gestion des tableaux et listes d’attente
déclenchement des exports / mails admin

"""

import asyncpg, os, time

from datetime import datetime, date, timezone
from core.config import TABLEAUX
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv(".env", override=False)
        
# load_dotenv()  # charge le fichier .env
# Variable globale (railway) on la priorité car il n'existe pas de .env 
# python ne trouve rien donc charge rien

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
# Gestion de le concordance des places Valide/Attente en fonction modification de Config.py
    
async def reaffectation_tableau(t):

    async with pool.acquire() as conn:
        conf = TABLEAUX[t]
        while True:
            ok_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM inscription_tableaux
                WHERE tableau=$1
                AND statut='OK'
            """, t)

            if ok_count >= conf["capacite"]:
                break

            attente = await conn.fetchrow("""
                SELECT licence
                FROM inscription_tableaux
                WHERE tableau=$1
                AND statut='ATTENTE'
                ORDER BY id
                LIMIT 1
            """, t)

            if not attente:
                break
            # print(f"Promotion {attente['licence']} -> {t}")
            await conn.execute("""
                UPDATE inscription_tableaux
                SET statut='OK'
                WHERE licence=$1
                AND tableau=$2
            """,
            attente["licence"],
            t
            )
            
async def reaffectation_all():
    for tableau in TABLEAUX:
        # print(f"  Reaffectation des tableaux des licenciés suivants : {tableau}")
        await reaffectation_tableau(tableau)

# fin de cette gestion 
    
pool = None

#  init pool

async def init_db_pool():
    
    global pool
    if DATABASE_URL and "localhost" in DATABASE_URL:
        # Local (pas de SSL)
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5
        )
    else:
        # Production (Railway ou Neon → SSL obligatoire)
        
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            ssl="require"
        )
# print(" Creation tables si besoin")
#  init DB

async def init_db():
    async with pool.acquire() as conn:
        
        # créer la séquence
        await conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS dossard_seq START 1;
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS inscriptions (
            id SERIAL PRIMARY KEY, dossard INTEGER DEFAULT nextval('dossard_seq'), licence TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL , prenom TEXT NOT NULL, club TEXT, points INTEGER NOT NULL, paiement TEXT, mail TEXT, 
            date_inscription TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            event_id INT DEFAULT 1
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS inscription_tableaux (
            id SERIAL PRIMARY KEY, licence TEXT NOT NULL, tableau TEXT, statut TEXT,
            event_id INT DEFAULT 1, UNIQUE(licence, tableau, event_id)
        )
        """)
        
        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tableau_event 
        ON inscription_tableaux (tableau, event_id);
        """)
        
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS mail_control (
            id INT PRIMARY KEY DEFAULT 1,
            last_admin_mail DATE,
            last_count INT
        )
        """)
        
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            licence TEXT,
            email TEXT NOT NULL,
            type_mail TEXT NOT NULL,
            event_id INT DEFAULT 1,
            subject TEXT,
            brevo_message_id TEXT,
            statut TEXT DEFAULT 'envoye',
            opened BOOLEAN DEFAULT FALSE
        )
        """)
        
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS delete_inscrit (
            id SERIAL PRIMARY KEY, dossard INT, licence TEXT NOT NULL, nom TEXT NOT NULL, prenom TEXT NOT NULL,
            club TEXT, points INT NOT NULL, mail TEXT, paiement TEXT, date_inscription TIMESTAMP, 
            date_suppression TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        #  Initialisation si vide
        
        await conn.execute("""
        INSERT INTO mail_control (id, last_admin_mail, last_count)
        VALUES (1, NULL, 0)
        ON CONFLICT (id) DO NOTHING
        """)

#  licence déjà inscrite

async def licence_exists(licence):
    async with pool.acquire() as conn:
        r = await conn.fetchrow(
            "SELECT 1 FROM inscriptions WHERE licence=$1",
            licence
        )
        return r is not None

#  toutes inscriptions

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

#  classement par tableau

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

#  comptage

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

#  comptage en attente

async def count_tableau_attente(t):
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM inscription_tableaux
            WHERE tableau=$1 AND statut='ATTENTE'
        """, t)

#  statut tableau

async def tableau_status(t):
    conf = TABLEAUX[t]
    used_ok = await count_tableau(t, "OK")
    used_att = await count_tableau_attente(t)
    if used_ok < conf["capacite"]:
        return "OK"
    if used_att < conf.get("attente", 0):
        return "ATTENTE"
    return "FULL"

#  sauvegarde inscription
    
async def save_inscription(data):
    start = time.time() # xxxx
    
    async with pool.acquire() as conn:
        async with conn.transaction():   # transaction globale
            
            # 1 insertion joueur
            
            t0 = time.time()
            try:
                await conn.execute("""
                INSERT INTO inscriptions
                (nom, prenom, club, points, licence,paiement, mail)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                data["nom"],
                data["prenom"],
                data["club"],
                int(data["points"]),
                data["licence"],
                data.get("paiement", ""),
                data["mail"]
                )
            except asyncpg.UniqueViolationError:
                raise ValueError("Licence déjà inscrite")  

            # print("INSERT INSCRIPTION =", round((time.time()-t0)*1000), "ms")
            # 2 insertion tableaux avec verrouillage
            
            for t in data["tableaux"]:
                
                # verrouille les lignes de ce tableau merci chatgpt
                t0 = time.time()
                await conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext($1))",
                t
                )                
                t0 = time.time()
                conf = TABLEAUX[t]
                counts = await conn.fetchrow("""
                    SELECT
                        COUNT(*) FILTER (WHERE statut='OK') AS ok_count,
                        COUNT(*) FILTER (WHERE statut='ATTENTE') AS attente_count
                    FROM inscription_tableaux
                    WHERE tableau=$1
                """, t)
                used_ok = counts["ok_count"]
                used_att = counts["attente_count"]

                if used_ok < conf["capacite"]:
                    status = "OK"
                elif used_att < conf.get("attente", 0):
                    status = "ATTENTE"
                else:
                    raise ValueError(f"{t} complet")
    
                t0 = time.time()
                await conn.execute("""
                INSERT INTO inscription_tableaux
                (licence, tableau, statut)
                VALUES ($1,$2,$3)
                """,
                data["licence"],
                t,
                status
                ) 
                # print(f"INSERT_TABLEAU {t} =", round((time.time()-t0)*1000), "ms")
            
#  promotion attente

async def promote_attente(t):
    async with pool.acquire() as conn:
        ok = await count_tableau(t, "OK")
        conf = TABLEAUX[t]
        if ok >= conf["capacite"]:
            return
        row = await conn.fetchrow("""
        SELECT licence FROM inscription_tableaux
        WHERE tableau=$1 AND statut='ATTENTE'
        ORDER BY id LIMIT 1
        """, t)

        if row:
            await conn.execute("""
            UPDATE inscription_tableaux
            SET statut='OK'
            WHERE licence=$1 AND tableau=$2
            """, row["licence"], t)

#  Tableau par licencie 

async def get_tableaux_by_licence(licence):
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
        SELECT tableau
        FROM inscription_tableaux
        WHERE licence=$1
        """, licence)
        return [r["tableau"] for r in rows]

#  connexion transaction

@asynccontextmanager
async def get_conn():
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

#  Check Envoi 

async def should_send_admin_mail(conn, current_count):

    row = await conn.fetchrow("""
        SELECT last_count
        FROM mail_control
        WHERE id=1
    """)
    
    # premier envoi si la ligne n'existe pas
    
    if not row:
        return True
    last_count = row["last_count"]
    
    # envoyer seulement si le nombre d'inscriptions a changé
    
    if current_count != last_count:
        return True
    return False
	
#  Mise a Jour  

async def update_admin_mail_status(conn, current_count):

    await conn.execute("""
        UPDATE mail_control
        SET last_admin_mail=$1, last_count=$2
        WHERE id=1
    """, date.today(), current_count)
    
async def init_archive_trigger():

    async with pool.acquire() as conn:
        trigger_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'before_delete_inscription'
            );
        """)

        if not trigger_exists:

            await conn.execute("""
            CREATE OR REPLACE FUNCTION archive_inscription()
            RETURNS TRIGGER AS $func$
            BEGIN
                INSERT INTO delete_inscrit (dossard, licence, nom, prenom, club, points, paiement,
                mail, date_inscription, date_suppression)
                VALUES (OLD.dossard, OLD.licence, OLD.nom, OLD.prenom, OLD.club,OLD.points,OLD.paiement,
                OLD.mail, OLD.date_inscription,NOW()
                );

                RETURN OLD;
            END;
            $func$ LANGUAGE plpgsql;

            CREATE TRIGGER before_delete_inscription
            BEFORE DELETE ON inscriptions
            FOR EACH ROW
            EXECUTE FUNCTION archive_inscription();
            """)

            print(" Trigger créé")
            
async def log_email(
    licence, email, type_mail, event_id, subject, brevo_message_id
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO email_logs (licence, email, type_mail, event_id, subject, brevo_message_id)
            VALUES ($1,$2,$3,$4,$5,$6)
            """,
            licence, email, type_mail, event_id, subject, brevo_message_id
        )
 
# reveil de la base             
async def wake_db():
    
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")
              