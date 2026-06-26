"""
Programme principal du comparatif Tournoi / HelloAsso

"""

import os
import glob

from config import FICHIER_SORTIE
from lecture_tournoi import lire_tournoi
from lecture_helloasso import lire_helloasso
from comparaison import comparer
from excel import creer_excel

def choisir_fichier(prefixe):
    downloads = os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )
    fichiers = glob.glob(
        os.path.join(downloads, f"{prefixe}*.xlsx")
    )
    if not fichiers:
        raise FileNotFoundError(
            f"Aucun fichier {prefixe}*.xlsx trouvé dans Downloads."
        )
    return max(fichiers, key=os.path.getmtime)

def main():

    print("=" * 60)
    print("COMPARATIF TOURNOI / HELLOASSO")
    print("=" * 60)
    print("Recherche du dernier fichier Inscriptions_Tournoi...")
    fichier_tournoi = choisir_fichier("Inscriptions_Tournoi")
    print(f"Fichier sélectionné : {os.path.basename(fichier_tournoi)}")
    print("Recherche du dernier fichier export-paiements...")
    fichier_hello = choisir_fichier("export-paiements")
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
