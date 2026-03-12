// ------------ RENDER TABLEAUX ---------------------

export function renderTableaux(TABLEAUX, places, joueurPoints){

    const isAdmin = document.cookie.includes("admin=1");
    const checked = Array.from(
        document.querySelectorAll("#tableauxContainer input:checked")
    ).map(cb => cb.value);
    const box = document.getElementById("tableauxContainer");
    if(!box || !TABLEAUX) return;
    box.innerHTML = Object.keys(TABLEAUX).map(key => {
        const conf = TABLEAUX[key];
        if(!conf) return "";
        const used   = places?.[key]?.ok ?? 0;
        const cap    = places?.[key]?.capacite ?? conf.capacite ?? 0;
        const att    = places?.[key]?.attente ?? 0;
        const attMax = places?.[key]?.attente_max ?? conf.attente ?? 0;
        const min = conf.min ?? null;
        const max = conf.max ?? null;
        let interdit = false;
        if(joueurPoints !== null){
            if(min !== null && joueurPoints < min) interdit = true;
            if(max !== null && joueurPoints > max) interdit = true;
        }
        let color = "green";
        let disabled = false;
        let badge = `${att}/${attMax}`;

        // ------------ règles état tableau ------------

        if(interdit){
            color = "grey";
            badge = `${att}/${attMax} ⛔️ Interdit`;
            disabled = true;
        }
        else if(att >= attMax){
            color = "red";
            badge = "🔒 COMPLET";
            disabled = true;
        }
        else if(used >= cap){
            color = "orange";
        }
        if(isAdmin) disabled = false;
        const isChecked = checked.includes(key) ? "checked" : "";
        return `
        <div class="tableau-row ${color} ${interdit ? "tableau-interdit" : ""}">
            <input type="checkbox"
                value="${key}"
                ${disabled ? "disabled" : ""}
                ${isChecked}
                onchange="limitSelection.call(this)">  
            <span class="col-tableau">${key}</span>
            <span class="col-tranche ${interdit ? "tranche-ko" : "tranche-ok"}">
                ${min ?? "-"}-${max ?? "-"}
            </span>
            <div class="tableau-stats">
                <span class="stat-inscrit">
                    🏓 Inscrit ${used}/${cap}
                </span>
                <span class="stat-attente">
                    ⏳ Attente ${badge}
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
