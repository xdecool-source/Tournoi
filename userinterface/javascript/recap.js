// Construit et affiche un résumé final de l’inscription 
// (joueur, email, tableaux, places restantes).

export async function showRecap(player, email, tableauxSel){

    //  0 sécurité

    if(!player){
        console.error("PLAYER UNDEFINED");
        return;
    }

    // 1 cacher les autres cartes

    document.getElementById("licenceCard")?.classList.add("hidden");
    document.getElementById("inscriptionCard")?.classList.add("hidden");

    const row = document.getElementById("inscriptionRow");
    if(row){
        row.style.display = "block";
    }

    // 2 reload config et places temps réel

    const conf = await fetch("/tableaux").then(r=>r.json());
    const placesNow = await fetch("/places").then(r=>r.json());

    let tableauxHTML = "";
    let total = 0; 

    tableauxSel.forEach(t=>{
        const c = conf[t];
        const p = placesNow[t];

        if(!c || !p){
            console.warn("MANQUANT", t);
            return;
        }

        const prix = Number(c.prix || 0);
        total += prix;

        const restantes = Math.max(0, p.capacite - p.ok);

        const range = (c.min != null && c.max != null)
            ? ` (${c.min}-${c.max} pts)`
            : "";

        let txt = "";
        let color = "green";

        if(p.ok >= p.capacite && p.attente >= p.attente_max){
            txt = `${p.capacite}/${p.capacite} et vous êtes le dernier en liste d'attente`;
            color = "red";
        }
        else if(p.ok >= p.capacite){
            txt = `${p.capacite}/${p.capacite} Vous êtes le (${p.attente}/${p.attente_max}) en liste d'attente`;
            color = "orange";
        }
        else{
            txt = `${restantes} places restantes`;
        }

        tableauxHTML += `
            <div style="margin:6px 0">
                <b>${t}</b>${range} - 💰 ${prix}€
                <br>
                <span style="color:${color}">
                    ${txt}
                </span>
            </div>
        `;
    });

    // 3 contenu recap

    const recapContent = document.getElementById("recapContent");

    if(recapContent){
        recapContent.classList.remove("hidden");
        recapContent.style.display = "block"; 

        // console.log("TOTAL TOTAL =", total, typeof total);

        if(total === 0){

            recapContent.innerHTML = `
                <b style="color:red; font-size:20px;">
                    ❌ Annulation Inscription
                </b>
                <br><br>

                <b>${player.prenom} ${player.nom}</b><br>
                N° de Licence: <b>${player.licence}</b><br>
                Licencié au Club: ${player.club}<br>
                Ayant ${player.points} Points dans cette Phase<br>
                Votre Adresse Mail: ${email}<br><br>

                Plus aucun tableau sélectionné
                <br><br>

                <b style="font-size:18px;">
                    Merci de nous envoyer votre RIB ou votre adresse pour le remboursement.
                    Les frais de timbre sont à votre charge. 
                </b>
                <br><br>

                <b style="color:#007bff;">
                    Un mail va suivre afin de confirmer votre annulation
                </b>
            `;

        }else{

            recapContent.innerHTML = `
                <b>${player.prenom} ${player.nom}</b><br>
                N° de Licence: <b>${player.licence}</b><br>
                Licencié au Club: ${player.club}<br>
                Ayant ${player.points} Points dans cette Phase<br>
                Votre Adresse Mail: ${email}<br><br>

                Liste des tableaux validés<br>
                ${tableauxHTML}

                <b style="font-size:18px; color:#28a745;">
                    Total : ${total}€
                </b>
                <br><br>

                <div style="text-align:center">
                    <div style="color:orange; font-size:14px; margin-bottom:10px;">
                        ⚠️ Merci de payer exactement ${total}€
                    </div>

                    <a href="https://www.helloasso.com/associations/tennis-de-table-thuirinois/evenements/tournoi-l-homopongistus"
                    target="_blank"
                    style="
                        display:inline-block;
                        padding:12px 25px;
                        background:#ffcc00;
                        color:black;
                        font-weight:bold;
                        border-radius:8px;
                        text-decoration:none;
                        margin-bottom:15px;
                    ">
                    💳 Payer maintenant
                    </a>
                </div>

                <br>

                <b style="color:#007bff;">
                Paiement obligatoire pour valider définitivement votre inscription
                la contribution HelloAsso est facultative et peut être modifiée.
                </b>

                <br><br>

                <b style="color:#007bff;">
                Un mail va suivre afin de confirmer vos Tableaux et Tarifs avec le lien de paiement
                </b>
            `;
        }
   }

    // 4 afficher recap (FIX COMPLET)
    
    const recapCard = document.getElementById("recapCard");

    if(recapCard){
        recapCard.classList.remove("hidden");
        recapCard.style.display = "block";
        recapCard.style.width = "100%";
        recapCard.style.height = "auto";
        recapCard.style.overflow = "visible";

        recapCard.scrollIntoView({ behavior: "smooth" }); // 🔥 UX
    }

    // console.log("RECAP OK", total);
}
