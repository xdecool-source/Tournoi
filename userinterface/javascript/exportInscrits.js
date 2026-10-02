import {
    createCard,
    createBadge,
    createPlayerRow
} from "/static/javascript/exportTemplates.js";

let inscritsGlobal = [];

async function chargerInscrits() {

    // credentials:"include" gestion admin password

    try {
        // chargement des inscrits
        const res = await fetch("/inscrits");
        const data = await res.json();
        if (!data.success) {alert(data.error || "Erreur");return;}
        const inscrits = data.inscrits || [];
                
        // On garde les inscrits en mémoire
        // pour pouvoir les trier sans refaire une requête serveur
        inscritsGlobal = inscrits;

        // chargement config tableaux
        const tableauxRes = await fetch("/tableaux");
        const tableauxConfig = await tableauxRes.json();
        const placesRes = await fetch("/places");
        const places = await placesRes.json();

        // compteurs tableaux
        const compteurs = {};

        for (const t in tableauxConfig) {
            compteurs[t] = 0;
        }

        // comptage inscriptions
        for (const p of inscrits) {
            for (const t of (p.tableaux || [])) {
                if (compteurs[t] !== undefined) {compteurs[t]++;}
            }
        }

        // cartes statistiques
        let statsHtml = `
            <div class="card">
                <p>Total inscrits <br></p>
                <h2 style="font-size:24px;color:#1976d2;">${inscrits.length}</h2>
                <br><br>Répartition :</div>`;

        for (const t in tableauxConfig) {
            const conf = tableauxConfig[t];
            const p = places[t] || {};
            const ok = Number(p.ok || 0);
            const attente = Number(p.attente || 0);
            const capacite = Number(p.capacite || 0);
            const attenteMax = Number(p.attente_max || 0);
            const reste = capacite - ok;
            const resteAttente = attenteMax - attente;

            // couleur dynamique
            let color = "#2e7d32";
            if (reste <= 2) {color = "#f57c00";}
            if (reste <= 0) {color = "#c62828";}

            // texte capacite
            let textePlaces = `
            <span style="font-size:20px;font-weight:bold;">${ok}/${capacite}</span><br>
            <span style="font-size:12px;font-weight:normal;color:#666;">Attente : ${attente}/${attenteMax}</span>`;

            // complet
            if (ok >= capacite &&attente >= attenteMax) {
                textePlaces = `
                <span style="font-size:18px;font-weight:bold;color:#c62828;">COMPLET</span><br>
                <span style="font-size:14px;font-weight:normal;color:#666;">Attente pleine</span>`;color = "#c62828";}

            // carte
            statsHtml += createCard({titre: t,contenu: textePlaces,footer:
                 `${conf.jour.label} - ${conf.jour.hour}`,color});}
        document.getElementById("statsContainer").innerHTML =statsHtml;

        // controles de tri
        document.getElementById("resultat").innerHTML = `
        <div style="margin:15px 0;padding:10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <label for="triInscrits"><strong>Trier par :</strong></label>
        <select id="triInscrits" style=" padding:7px 10px;border:1px solid #ccc;border-radius:6px;background:white;">
                    <option value="classement">Classement</option>
                    <option value="nom">Nom</option>
                    <option value="club">Club</option>
                    <option value="dossard">Dossard</option>
        </select>
        <select id="ordreTri" style=" padding:7px 10px;border:1px solid #ccc;border-radius:6px;background:white;">
                    <option value="asc">Croissant</option>
                    <option value="desc">Décroissant</option>
        </select>
        </div><div id="tableauInscrits"></div>`;

        // affichage initial
        afficherTableau(inscritsGlobal);

        // evenements tri
        document
            .getElementById("triInscrits")
            .addEventListener("change",trierInscrits);
        document
            .getElementById("ordreTri")
            .addEventListener("change",trierInscrits);
    } catch (err) {console.error(err);
        alert("Erreur serveur");
    }
}

// affichage du tableau
function afficherTableau(inscrits) {
    let html = `
        <table><thead><tr>
        <th>Dossard</th><th>Licence</th><th>Nom</th><th>Prénom</th>
        <th>Club</th><th>Classement</th><th>Tableaux</th>
        </tr>
        </thead>
        <tbody>
    `;

    // lignes joueurs
    for (const p of inscrits) {
        // badges tableaux

        const badges = (p.tableaux || [])
            .map(t => {
                const attente = t.includes("_ATTENTE");
                const nom = t.replace("_ATTENTE", "");
                return createBadge(nom,attente);
            })
            .join("");

        // badge annulation
        const badgeAnnule =
            p.annule === true ||
            p.annule === "t" ||
            p.annule === "true"
                ? `
                    <span style="
                    background:#c62828;color:white;padding:4px 8px;border-radius:6px;
                    font-size:12px;font-weight:bold;margin-left:4px;">ANNULÉ</span>`: "";

        // ligne joueur
        html += createPlayerRow(p,badges + badgeAnnule);}

    // fermeture tableau
    html += `</tbody></table>`;

    // injection html
    document.getElementById("tableauInscrits").innerHTML = html;

}

// tri des inscrits
function trierInscrits() {
    const critere = document.getElementById("triInscrits").value;
    const ordre = document.getElementById("ordreTri").value;

    // Copie du tableau pour ne pas modifier
    // inscritsGlobal directement
    const tries = [...inscritsGlobal].sort((a, b) => {
        let valeurA;
        let valeurB;

        // nom
        if (critere === "nom") {
            valeurA =
                String(a.nom || "")
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase();

            valeurB =
                String(b.nom || "")
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase();
        }

        // classement
        else if (critere === "classement") {
            valeurA =
                Number(a.points) || 0;
            valeurB =
                Number(b.points) || 0;
        }

        // club
        else if (critere === "club") {
            valeurA =
                String(a.club || "")
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase();
            valeurB =
                String(b.club || "")
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase();
        }

        // dossard
        else if (critere === "dossard") {valeurA = Number(a.dossard) || 0;valeurB = Number(b.dossard) || 0;}

        // comparaison
        if (valeurA < valeurB) {return ordre === "asc" ? -1 : 1;}
        if (valeurA > valeurB) {return ordre === "asc" ? 1 : -1;}
        return 0;
    });

    // rafraichissement du tableau
    afficherTableau(tries);

}

// export

window.chargerInscrits = chargerInscrits;
