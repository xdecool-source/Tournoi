// Génère l’interface des tableaux
//  (avec règles, états, sélection limitée et visuel dynamique).

// ------------ RENDER TABLEAUX ---------------------

export function renderTableaux(
    TABLEAUX,
    places,
    joueurPoints,
    alreadyInscrit = false,
    tableauxInscrits = []
){

    const isAdmin = document.cookie.includes("admin=1");
    const box = document.getElementById("tableauxContainer");
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

        // ----------- règles métier -----------

        let interdit = false;
        if(!isNaN(points)){
            if(min !== null && points < min) interdit = true;
            if(max !== null && points > max) interdit = true;
        }

        let color = "green";
        let disabled = false;
        let attenteLabel = `${att}/${attMax}`;

        // ----------- états tableau -----------

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

        // ----------- blocage si déjà inscrit -----------

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
                ${disabled ? "disabled" : ""}
                ${isChecked ? "checked" : ""}
                onchange="limitSelection.call(this)">  
            <span class="col-tableau">${key}</span>
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
    if(e.target.matches('#tableauxContainer input[type="checkbox"]')){
        const card = e.target.closest(".tableau-row");
        if(e.target.checked){
            card.classList.add("selected");
        }else{
            card.classList.remove("selected");
        }
    }
});
