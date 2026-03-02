from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv()

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