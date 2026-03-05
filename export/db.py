
#  chercher toutes les inscriptions par exemple pour générer l’Excel des inscrits

import os
import psycopg2

from psycopg2.extras import DictCursor
from dotenv import load_dotenv

load_dotenv(".env", override=False)
if os.getenv("ENV") != "production":
    print("Mode dev")
        
# load_dotenv()  # charge le fichier .env
# Variable globale (railway) on la priorité car il n'existe pas de .env 
# python ne trouve rien donc charge rien 

QUERY = """
SELECT 
    i.id,
    i.nom || ' ' || i.prenom AS "Nom Prénom",
    i.club AS "Club",
    i.points AS "Classement",
    i.licence AS "Licence",
    i.mail AS "Mail",
    it.tableau,
    it.statut
FROM inscriptions i
JOIN inscription_tableaux it 
    ON i.licence = it.licence
ORDER BY i.id, it.tableau;
"""

def fetch_inscriptions():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL manquante")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute(QUERY)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows