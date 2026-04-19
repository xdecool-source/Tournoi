# Prix dans confi.py
# Calcul des prix pour la feuille 

from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.drawing.image import Image
from core.config import TABLEAUX
from pathlib import Path

def create_price_sheet(wb, data_joueurs, root_dir):

    ws = wb.create_sheet("Prix")
    
#  Logo Tournoi   

    image_path = root_dir / "ressources" / "Tournoi.jpg"
    if image_path.exists():
        img = Image(str(image_path))
        img.width = 600
        img.height = 110
        ws.add_image(img, "C1")

    start_row = 8
    total_valide_general = 0
    total_attente_general = 0
    lignes_prix = []

#  Calcul des montants 

    for dossard, infos in sorted(data_joueurs.items()):
        montant_valide = 0
        montant_attente = 0
        for tableau, statut in infos["Inscriptions"]:
            prix = TABLEAUX.get(tableau, {}).get("prix", 0)
            if statut.upper() == "OK":
                montant_valide += prix
            elif statut.upper() == "ATTENTE":
                montant_attente += prix
        total_valide_general += montant_valide
        total_attente_general += montant_attente
        lignes_prix.append([
            dossard,
            infos["Nom"],
            infos.get("Licence", ""),
            ", ".join([f"{t} ({s})" for t, s in infos["Inscriptions"]]),
            montant_valide,
            montant_attente
        ])

#  Totaux 

    ws[f"A{start_row}"] = "Montants par joueur"
    ws[f"A{start_row}"].font = Font(bold=True, size=14)
    ws[f"A{start_row+1}"] = "Total encaissé (validés) :"
    ws[f"A{start_row+2}"] = "Total en attente :"
    ws[f"E{start_row+1}"] = total_valide_general
    ws[f"F{start_row+2}"] = total_attente_general
    ws[f"E{start_row+1}"].number_format = '#,##0.00 €'
    ws[f"F{start_row+2}"].number_format = '#,##0.00 €'
    ws[f"E{start_row+1}"].font = Font(bold=True)
    ws[f"F{start_row+2}"].font = Font(bold=True)
    ws[f"A{start_row+1}"].font = Font(bold=True)
    ws[f"A{start_row+2}"].font = Font(bold=True)

#  Tableau Détaillé 

    header_row = start_row + 4
    headers = [
        "Dossard",
        "Nom Prénom",
        "N° Licence",
        "Tableaux",
        "Montant validé (€)",
        "Montant en attente (€)"
    ]

    for col_index, value in enumerate(headers, 1):
        ws.cell(row=header_row, column=col_index, value=value).font = Font(bold=True)
    data_row = header_row + 1
    light_gray = PatternFill(start_color="F2F2F2", fill_type="solid")

    for index, ligne in enumerate(lignes_prix):
        for col_index, value in enumerate(ligne, 1):
            ws.cell(row=data_row, column=col_index, value=value)
            
        ws[f"B{data_row}"].font = Font(bold=True)
        ws[f"E{data_row}"].number_format = '#,##0.00 €'
        ws[f"F{data_row}"].number_format = '#,##0.00 €'
        ws[f"E{data_row}"].font = Font(bold=True)

        if index % 2 == 0:
            for col in range(1, 7):
                ws.cell(row=data_row, column=col).fill = light_gray
        ws[f"A{data_row}"].alignment = Alignment(horizontal="center")
        data_row += 1
    ws.freeze_panes = f"A{header_row+1}"

#  Auto largeur 

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2