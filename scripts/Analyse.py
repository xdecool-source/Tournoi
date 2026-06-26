"""
Programme principal du comparatif Tournoi / HelloAsso

"""

import os
from tkinter import Tk, filedialog

from config import FICHIER_SORTIE
from lecture_tournoi import lire_tournoi
from lecture_helloasso import lire_helloasso
from comparaison import comparer
from excel import creer_excel

def choisir_fichier(titre):
    downloads = os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )

    fichier = filedialog.askopenfilename(
        title=titre,
        initialdir=downloads,
        filetypes=[("Fichiers Excel", "*.xlsx")]
    )

    if not fichier:
        raise SystemExit("Sélection annulée.")

    return fichier

def main():

    root = Tk()
    root.withdraw()

    print("=" * 60)
    print("COMPARATIF TOURNOI / HELLOASSO")
    print("=" * 60)
    print()
    print("Sélection du fichier Inscription_Tournoi...date")

    fichier_tournoi = choisir_fichier(
        "Sélectionnez le fichier Tournoi"
    )

    print(f"Fichier sélectionné : {os.path.basename(fichier_tournoi)}")
    print()
    print("Sélection du fichier export-paiements... date : de HelloAsso")
    print()

    fichier_hello = choisir_fichier(
        "Sélectionnez le fichier HelloAsso"
    )

    print(f"Fichier sélectionné : {os.path.basename(fichier_hello)}")

    tournoi = lire_tournoi(fichier_tournoi)
    hello = lire_helloasso(fichier_hello)

    comparatif, stats = comparer(
        tournoi,
        hello
    )

    creer_excel(
        comparatif,
        stats,
        FICHIER_SORTIE
    )

    print()
    print("Comparatif terminé.")
    print(f"Fichier créé : {FICHIER_SORTIE}")
    print()
    print("Résumé")
    print("-" * 40)
    print(f"Joueurs tournoi     : {len(tournoi)}")
    print(f"Paiements HelloAsso : {len(hello)}")
    print(f"OK                  : {stats['ok']}")
    print(f"Différences         : {stats['difference']}")
    print(f"Sans paiement       : {stats['sans_paiement']}")
    print(f"Paiements orphelins : {stats['orphelin']}")
    print(f"Total Tournoi       : {stats['total_tournoi']:.2f} €")
    print(f"Total HelloAsso     : {stats['total_hello']:.2f} €")
    print(f"Écart Global        : {stats['total_hello']-stats['total_tournoi']:.2f} €")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print("ERREUR :", e)
        input("Appuyez sur Entrée pour quitter...")
