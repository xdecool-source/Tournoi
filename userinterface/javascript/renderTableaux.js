// Génère l’interface des tableaux
//  (avec règles, états, sélection limitée et visuel dynamique).

//  Render Tableaux 

export function renderTableaux(
    TABLEAUX,
    places,
    joueurPoints,
    alreadyInscrit = false,
    tableauxInscrits = [],
    isAdmin = false  
){

    // const isAdmin = document.cookie.includes("admin=1");
    const box = document.getElementById("tableauxContainer");
    // console.log("IS ADMIN RENDER:", isAdmin);
    if(!box || !TABLEAUX) return;

    const points = Number(joueurPoints);
    box.innerHTML = Object.keys(TABLEAUX).map(key => {
        const conf = TABLEAUX[key];
        if(!conf) return "";
        const used   = places?.[key]?.ok ?? 0;
        const cap    = places?.[key]?.capacite ?? conf.capacite ?? 0;
        const att    = places?.[key]?.attente ?? 0;
        const attMax = places?.[key]?.attente_max ?? conf.attente ?? 0;
        const min = conf.min != null ? Number(conf.min) : null;
        const max = conf.max != null ? Number(conf.max) : null;
        const isChecked = tableauxInscrits.includes(key);

        //  règles métier 

        let interdit = false;
        if(!isNaN(points)){
            if(min !== null && points < min) interdit = true;
            if(max !== null && points > max) interdit = true;
        }

        let color = "green";
        let disabled = false;
        let attenteLabel = `${att}/${attMax}`;

        //  états tableau 

        if(interdit){
            color = "grey";
            attenteLabel = `${att}/${attMax} ⛔️ `;
            disabled = true;
        }
        else if(att >= attMax){
            color = "red";
            attenteLabel = "🔒 COMPLET";
            disabled = true;
        }
        else if(used >= cap){
            color = "orange";
        }

        //  blocage si déjà inscrit 

        if(alreadyInscrit && !isAdmin){
            disabled = true;
            if(isChecked){
                attenteLabel = `${att}/${attMax} 🔒 Déjà inscrit`;
            }
        }

        // admin override

        if(isAdmin){
            disabled = false;
        }
        return `
        <div class="tableau-row ${color} ${isChecked ? "selected" : ""} ${interdit ? "tableau-interdit" : ""} ${alreadyInscrit && !isAdmin ? "locked" : ""}">  
            <input type="checkbox"
                value="${key}"
                data-prix="${conf.prix ?? 0}"
                ${disabled ? "disabled" : ""}
                ${isChecked ? "checked" : ""}
                onchange="limitSelection.call(this)">  

            <span class="col-tableau">
                ${key} - 💰 ${conf.prix ?? 0}€
            </span>
            <span class="col-tranche ${interdit ? "tranche-ko" : "tranche-ok"}">
                ${conf.label ?? (min !== null && max !== null ? `${min}-${max}` : "")}
            </span>
            <div class="tableau-stats">
                <span class="stat-inscrit">
                    🏓 Inscrit ${used}/${cap}
                </span>
                <span class="stat-attente">
                    ⏳ Attente : ${att} / ${attMax}
                    ${isChecked && alreadyInscrit && !isAdmin ? ' <span class="badge-inscrit">🔒 inscrit</span>' : ''}
                </span>
            </div>
        </div>`;
    }).join("");
}

export function limitSelection(){

    const checked = document.querySelectorAll(
        "#tableauxContainer input:checked"
    );
    if(checked.length > 4){
        this.checked = false;
        openModal("Maximum 4 tableaux");
    }
}

window.limitSelection = limitSelection;

// gestion visuelle sélection

document.addEventListener("change", function(e){

    if(!e.target.matches('#tableauxContainer input[type="checkbox"]')){
        return;
    }

    let total = 0;
    document.querySelectorAll(
        "#tableauxContainer input:checked"
    ).forEach(cb => {
        const prix = parseInt(cb.dataset.prix || "0", 10);
        total += isNaN(prix) ? 0 : prix;
    });
    const el = document.getElementById("totalPrix");
    if(el){
        el.innerText = "Total : " + total + "€";
    }
    // console.log("TOTAL =", total); 
});
