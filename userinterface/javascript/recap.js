// Construit et affiche un résumé final de l’inscription 
// (joueur, email, tableaux, places restantes).

export async function showRecap(player, email, tableauxSel){

    // 1 cacher les autres cartes
    document.getElementById("licenceCard")?.classList.add("hidden");
    document.getElementById("inscriptionCard")?.classList.add("hidden");
    // 2 reload config et places temps réel
    const confRaw = await fetch("/tableaux").then(r=>r.json());
    const conf = confRaw.tableaux || confRaw;   //  correction structure
    const placesNow = await fetch("/places").then(r=>r.json());
    let tableauxHTML = "";
    tableauxSel.forEach(t=>{
        const c = conf[t];
        const p = placesNow[t];
        if(!c || !p) return;
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
            color = "green";
        }
        tableauxHTML += `
            <div style="margin:6px 0">
                <b>${t}</b>${range}
                <br>
                <span style="color:${color}">
                    ${txt}
                </span>
            </div>
        `;
    });

    // 3 contenu recap (structure conservée)
    document.getElementById("recapContent").classList.remove("hidden");
    document.getElementById("recapContent").innerHTML = `
        <b>${player.prenom} ${player.nom}</b><br>
        N° de Licence: <b>${player.licence}</b><br>
        Licencié au Club: ${player.club}<br>
        Ayant ${player.points} Points en Phase 2<br>
        Votre Adresse Mail: ${email}<br><br>
        ✌️Liste des tableaux validés<br>
        ${tableauxHTML}
        <br><br>
        <b style="color:#007bff;">
        Un mail va suivre afin de confirmer votre inscription
        </b>
        <br><br>
            `;

    // 4 afficher recap
    document.getElementById("recapCard")?.classList.remove("hidden");
}
