"""
1. Récupère dans la base  :

inscriptions ;  suppressions.
rows = fetch_inscriptions()
deleted_rows = get_deleted_inscriptions()

2. Prépare les données
build_data(rows)
Organise les joueurs et les tableaux pour l'export.

3. Construit le classeur Excel
Je crée toutes les feuilles :
Joueurs
Tableaux
Une feuille par tableau
Prix
Suppression

4. Génère le fichier en mémoire
stream = BytesIO()
wb.save(stream)
Aucun fichier .xlsx n'est créé sur le disque.
Je garde Le classeur en mémoire dans un objet BytesIO.

5. Retourne le flux
Il renvoie :return stream
et je peux par la suite 
téléchargé par FastAPI ;
ou envoyé en pièce jointe d'un email ;
ou sauvegardé si besoin.

"""

from openpyxl import Workbook
from export.db import fetch_inscriptions, get_deleted_inscriptions
from export.excel_builder import (
    build_data,
    create_players_sheet,
    create_table_sheets,
    create_tableaux_sheet,
    create_deleted_sheet
)
from export.price import create_price_sheet
from io import BytesIO
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent

def generate():
    
  # si DB down on sort  
    try:
        rows = fetch_inscriptions()
        deleted_rows =  get_deleted_inscriptions()
        
        if not rows:
            print("Aucune donnée.")
            return None

        data_by_table, data_joueurs = build_data(rows)
        wb = Workbook()
        wb.remove(wb.active)
        create_players_sheet(wb, data_joueurs)
        create_table_sheets(wb, data_by_table)
        create_tableaux_sheet(wb, data_by_table)
        create_price_sheet(wb, data_joueurs,root_dir)
        create_deleted_sheet(wb, deleted_rows)

    #  génération en mémoire

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        
    #  libere memoire
        
        wb.close()  
        print(" Excel généré en mémoire")
        return stream

    except Exception as e:
        # log propre ici
        print(f"Erreur génération Excel: {e}")
        return None