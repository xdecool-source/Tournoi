from pathlib import Path
from openpyxl import Workbook

from export.db import fetch_inscriptions
from export.excel_builder import (
    build_data,
    create_players_sheet,
    create_table_sheets,
    create_tableaux_sheet
)
from export.price import create_price_sheet
from export.excel_builder import create_tableaux_sheet

ROOT_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = ROOT_DIR / "inscription"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
FINAL_FILE = EXPORT_DIR / "Inscription.xlsx"


def generate():
    rows = fetch_inscriptions()

    if not rows:
        print("Aucune donnée.")
        return

    data_by_table, data_joueurs = build_data(rows)

    wb = Workbook()
    wb.remove(wb.active)

    create_players_sheet(wb, data_joueurs)
    create_table_sheets(wb, data_by_table)
    create_tableaux_sheet(wb, data_by_table)
    create_price_sheet(wb, data_joueurs, ROOT_DIR)

    wb.save(FINAL_FILE)
    print("✅ Fichier généré :", FINAL_FILE)


if __name__ == "__main__":
    generate()