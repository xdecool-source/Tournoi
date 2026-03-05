
# génère le fichier Excel des inscriptions du tournoi
# Organisation par joueur et par tableau 
# pour construire les différentes feuilles Excel 
# (Joueurs, Tableaux, statistiques, prix).

import os

from openpyxl import Workbook
from services.db import get_all
from export.price import create_price_sheet
from core.config import FINAL_FILE, ROOT_DIR
from export.excel_builder import (
    build_data,
    create_players_sheet,
    create_table_sheets,
    create_tableaux_sheet
)

FINAL_FILE = "/tmp/Inscriptions.xlsx"


async def generate():

    print("STEP A - récupération DB")
    inscriptions = await get_all()
    if not inscriptions:
        print("Aucune donnée.")
        return None

    # ---------- transformation pour excel_builder ----------
    rows = []
    i = 1   # ← AJOUT ICI
    for joueur in inscriptions:
        tableaux = joueur.get("tableaux", [])
        for t in tableaux:
            rows.append({
                "id": joueur.get("id"),   # ← AJOUT ICI
                "Licence": joueur.get("licence"),
                "Nom Prénom": f"{joueur.get('nom')} {joueur.get('prenom')}",
                "Club": joueur.get("club"),
                "Points": joueur.get("points"),
                "Classement": joueur.get("classement", ""),   # ← AJOUT
                "Mail": joueur.get("mail", ""),   # ← AJOUT ICI
                "tableau": t,
                "statut": "OK"
            })
            i += 1

    print("STEP B - construction excel")
    data_by_table, data_joueurs = build_data(rows)
    wb = Workbook()
    wb.remove(wb.active)
    create_players_sheet(wb, data_joueurs)
    create_table_sheets(wb, data_by_table)
    create_tableaux_sheet(wb, data_by_table)
    create_price_sheet(wb, data_joueurs, ROOT_DIR)

    # ---------- sauvegarde disque ----------
    wb.save(FINAL_FILE)
    print("✅ Excel généré :", FINAL_FILE)