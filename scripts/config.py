"""
Configuration générale du comparatif Tournoi / HelloAsso
"""

import os

# Dossier où sera créé le fichier résultat

DOSSIER_SORTIE = os.path.join(
    os.path.expanduser("~"),
    "Downloads"
)

FICHIER_SORTIE = os.path.join(
    DOSSIER_SORTIE,
    "Comparatif_HelloAsso_Inscription_Tournoi.xlsx"
)

# Feuilles Excel

FEUILLE_TOURNOI = "Prix"
FEUILLE_HELLOASSO = "Feuille 1"

# Colonnes du fichier Tournoi

COLONNE_LICENCE = "N° Licence"
COLONNE_JOUEUR = "Nom Prénom"
COLONNE_TABLEAUX = "Tableaux"
COLONNE_PAIEMENT = "Paiement"
COLONNE_MONTANT = "Montant validé (€)"

# Colonnes HelloAsso

COLONNE_DESIGNATION = "Désignation"
COLONNE_TOTAL = "Montant total"
COLONNE_STATUT = "Statut du paiement"
STATUT_VALIDE = "Payé"

# Création automatique du dossier

os.makedirs(
    DOSSIER_SORTIE,
    exist_ok=True
)
