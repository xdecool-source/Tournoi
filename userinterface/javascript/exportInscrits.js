
import {
    createCard,
    createBadge,
    createPlayerRow
}
from "/static/javascript/exportTemplates.js";

async function chargerInscrits(){

// credentials:"include" gestion admin password

    try{

        // Chargement inscrits

        const res = await fetch("/inscrits");
        const data = await res.json();
        if(!data.success){
            alert(data.error || "Erreur");
            return;
        }
        const inscrits = data.inscrits || [];

        // Chargement config tableaux

        const tableauxRes = await fetch("/tableaux");
        const tableauxConfig = await tableauxRes.json();
        const placesRes = await fetch("/places");
        const places = await placesRes.json();

        // Compteurs tableaux

        const compteurs = {};
        for(const t in tableauxConfig){
            compteurs[t] = 0;
        }

        // Comptage inscriptions

        for(const p of inscrits){
            for(const t of (p.tableaux || [])){
                if(compteurs[t] !== undefined){
                    compteurs[t]++;
                }
            }
        }

        // Cartes statistiques

        let statsHtml = `
            <div class="card">
                <p>
                    Total inscrits <br>
                </p>
                <h2 style="
                    font-size:24px;
                    color:#1976d2;
                ">
                    ${inscrits.length}
                </h2>
                <br><br>
                    Répartition :
            </div>
        `;

        for(const t in tableauxConfig){

            const conf = tableauxConfig[t];
            const p = places[t] || {};
            const ok = Number(p.ok || 0);
            const attente = Number(p.attente || 0);
            const capacite = Number(p.capacite || 0);
            const attenteMax = Number(p.attente_max || 0);
            const reste = capacite - ok;
            const resteAttente = attenteMax - attente;

            // Couleur dynamique

            let color = "#2e7d32";
            if(reste <= 2){
                color = "#f57c00";
            }
            if(reste <= 0){
                color = "#c62828";
            }

            // Texte capacité

            let textePlaces = `

                <span style="
                    font-size:20px;
                    font-weight:bold;
                ">
                    ${ok}/${capacite}
                </span>
                <br>
                <span style="
                    font-size:12px;
                    font-weight:normal;
                    color:#666;
                ">
                    Attente : ${attente}/${attenteMax}
                </span>
            `;

            if(
                ok >= capacite &&
                attente >= attenteMax
            ){

                textePlaces = `

                    <span style="
                        font-size:18px;
                        font-weight:bold;
                        color:#c62828;
                    ">
                        COMPLET
                    </span>
                    <br>
                    <span style="
                        font-size:14px;
                        font-weight:normal;
                        color:#666;
                    ">
                        Attente pleine
                    </span>
                `;

                color = "#c62828";
            }

            statsHtml += createCard({

                titre: t,
                contenu: textePlaces,
                footer: `
                    ${conf.jour.label}
                    -
                    ${conf.jour.hour}
                `,

                color
            });
        }

        document.getElementById("statsContainer").innerHTML =
            statsHtml;

        // Construction tableau HTML

        let html = `
            <table>
                <thead>
                    <tr>
                        <th>dossard</th>
                        <th>Licence</th>
                        <th>Nom</th>
                        <th>Prénom</th>
                        <th>Club</th>
                        <th>Points</th>
                        <th>Tableaux</th>
                    </tr>
                </thead>
                <tbody>
        `;

        // Lignes joueurs

        for(const p of inscrits){

            const badges = (p.tableaux || [])
            .map(t => {
                const attente =
                    t.includes("_ATTENTE");
                const nom =
                    t.replace("_ATTENTE", "");
                return createBadge(
                    nom,
                    attente
                );
            })
            .join("");
            
            // ajout badge annulation

            const badgeAnnule =
                p.annule === true ||
                p.annule === "t" ||
                p.annule === "true"
                    ? `
                        <span style="
                            background:#c62828;
                            color:white;
                            padding:4px 8px;
                            border-radius:6px;
                            font-size:12px;
                            font-weight:bold;
                            margin-left:4px;
                        ">
                            ANNULÉ
                        </span>
                    `
                    : "";

            html += createPlayerRow(
                p,
                badges + badgeAnnule
            );

        }

        // Fermeture tableau

        html += `
                </tbody>
            </table>
        `;

        // Injection HTML

        document.getElementById("resultat").innerHTML =
            html;
        }catch(err){
            console.error(err);
            alert("Erreur serveur");
        }
        }
    
window.chargerInscrits = chargerInscrits;