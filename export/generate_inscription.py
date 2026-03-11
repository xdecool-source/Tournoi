# Génération du fichier Excel des Inscriptions 
# Sauvegarde en memoir du fichier Excel
# Pour un envoi par mail selon l'algo suivant  
# dernier mail n'a pas été envoyé aujourd'hui
# et nombre d'inscriptions a changé
# attention derniere journée pas d'envoi de mail donc pas de fichier jour
# il faut lancer le batch !!!!!

#from pathlib import Path
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

# --------- génération en mémoire
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    # ------ libere memoire 
    wb.close()  
    print("✅ Excel généré en mémoire")
    return stream