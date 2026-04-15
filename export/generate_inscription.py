# Génération du fichier Excel des Inscriptions 
# Sauvegarde en memoire du fichier Excel
# Pour un envoi par mail selon l'algo suivant  

from openpyxl import Workbook
from export.db import fetch_inscriptions
from export.excel_builder import (
    build_data,
    create_players_sheet,
    create_table_sheets,
    create_tableaux_sheet
)
from export.price import create_price_sheet
from io import BytesIO
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent

def generate():
  
  # si DB down on sort  
    try:
        rows = fetch_inscriptions()
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