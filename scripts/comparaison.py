"""
comparaison.py
Comparaison des données Tournoi / HelloAsso
"""


def comparer(tournoi, hello):
    """
    Compare les inscriptions tournoi et les paiements HelloAsso.
    Retourne :
        comparatif : liste de dictionnaires
        stats : statistiques globales
    """

    comparatif = []

    stats = {
        "ok": 0,
        "difference": 0,
        "sans_paiement": 0,
        "orphelin": 0,
        "total_tournoi": 0.0,
        "total_hello": 0.0,
    }

    licences = sorted(set(tournoi.keys()) | set(hello.keys()))

    for licence in licences:

        t = tournoi.get(licence)
        h = hello.get(licence)

        # Présent dans les deux fichiers
        if t and h:

            manquants = sorted(t["tableaux"] - h["tableaux"])
            en_trop = sorted(h["tableaux"] - t["tableaux"])

            ecart = round(
                h["montant"] - t["montant"],
                2
            )

            stats["total_tournoi"] += t["montant"]
            stats["total_hello"] += h["montant"]

            if ecart == 0 and not manquants and not en_trop:
                statut = "OK"
                stats["ok"] += 1
            elif ecart < 0:
                statut = "Complément"
                stats["difference"] += 1
            elif ecart > 0:
                statut = "Remboursement"
                stats["difference"] += 1
            else:
                statut = "Tableaux différents"
                stats["difference"] += 1

            comparatif.append({
                "licence": licence,
                "joueur": t["joueur"],
                "tableaux_tournoi": ", ".join(sorted(t["tableaux"])),
                "tableaux_hello": ", ".join(sorted(h["tableaux"])),
                "manquants": ", ".join(manquants),
                "en_trop": ", ".join(en_trop),
                "montant_tournoi": t["montant"],
                "montant_hello": h["montant"],
                "ecart": ecart,
                "statut": statut
            })

        # Inscription sans paiement
        elif t:

            stats["sans_paiement"] += 1
            stats["total_tournoi"] += t["montant"]

            comparatif.append({
                "licence": licence,
                "joueur": t["joueur"],
                "tableaux_tournoi": ", ".join(sorted(t["tableaux"])),
                "tableaux_hello": "",
                "manquants": ", ".join(sorted(t["tableaux"])),
                "en_trop": "",
                "montant_tournoi": t["montant"],
                "montant_hello": 0.0,
                "ecart": -t["montant"],
                "statut": "Pas de paiement"
            })

        # Paiement sans inscription
        else:

            stats["orphelin"] += 1
            stats["total_hello"] += h["montant"]

            comparatif.append({
                "licence": licence,
                "joueur": h["joueur"],
                "tableaux_tournoi": "",
                "tableaux_hello": ", ".join(sorted(h["tableaux"])),
                "manquants": "",
                "en_trop": ", ".join(sorted(h["tableaux"])),
                "montant_tournoi": 0.0,
                "montant_hello": h["montant"],
                "ecart": h["montant"],
                "statut": "Paiement sans inscription"
            })

    return comparatif, stats
    
